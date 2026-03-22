"""Agent 2: explainable competitive vulnerability analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from statistics import mean
from typing import Any


_PRICE_RE = re.compile(r"\$([\d,]+(?:\.\d{1,2})?)")

_KEYWORD_BUCKETS: dict[str, tuple[str, ...]] = {
	"ai_momentum": ("ai", "automation", "assistant", "copilot", "agent"),
	"enterprise_readiness": (
		"enterprise",
		"scim",
		"sso",
		"compliance",
		"governance",
		"audit",
		"security",
	),
	"integration_strength": (
		"integration",
		"api",
		"salesforce",
		"slack",
		"jira",
		"hubspot",
		"sync",
	),
}

# Weighted rubric. Each component is scored in [0, 1] and multiplied by weight.
_COMPONENT_WEIGHTS: dict[str, float] = {
	"pricing_pressure": 0.28,
	"segment_coverage": 0.22,
	"feature_depth": 0.18,
	"strategic_signals": 0.20,
	"business_model_pressure": 0.12,
}


@dataclass
class ScoreComponent:
	name: str
	weight: float
	score: float
	weighted_score: float
	reasoning: str


@dataclass
class VulnerabilityResult:
	company: str
	vulnerability_score: float
	risk_level: str
	confidence: float
	reasoning_summary: str
	detailed_reasoning: list[str]
	decision_trace: list[str]
	component_breakdown: list[ScoreComponent]
	signals: dict[str, int]
	metrics: dict[str, Any]
	scraped_at: str
	peer_rank: int | None
	peer_percentile: float | None


def _clamp01(value: float) -> float:
	return max(0.0, min(1.0, value))


def _parse_price(value: str | None) -> float | None:
	if not value:
		return None
	match = _PRICE_RE.search(value)
	if not match:
		return None
	return float(match.group(1).replace(",", ""))


def _bucket(score: float) -> str:
	if score >= 0.8:
		return "critical"
	if score >= 0.65:
		return "high"
	if score >= 0.45:
		return "medium"
	return "low"


def _extract_signal_counts(plans: list[dict[str, Any]]) -> dict[str, int]:
	feature_blob = " ".join(
		feature.lower() for plan in plans for feature in plan.get("features", [])
	)
	counts: dict[str, int] = {}
	for name, keywords in _KEYWORD_BUCKETS.items():
		counts[name] = sum(feature_blob.count(keyword) for keyword in keywords)
	return counts


def _score_pricing_pressure(
	pricing_summary: dict[str, Any],
	numeric_prices: list[float],
) -> tuple[float, str]:
	score = 0.0
	details: list[str] = []

	if pricing_summary.get("free_tier"):
		score += 0.35
		details.append("free tier present")

	if numeric_prices:
		min_price = min(numeric_prices)
		max_price = max(numeric_prices)
		if min_price <= 10:
			score += 0.40
			details.append(f"low entry point (${min_price:.2f})")
		elif min_price <= 20:
			score += 0.22
			details.append(f"moderate entry point (${min_price:.2f})")

		spread = max_price - min_price
		if spread >= 25:
			score += 0.25
			details.append(f"wide spread (${spread:.2f})")
		elif spread >= 12:
			score += 0.12
			details.append(f"mid spread (${spread:.2f})")

	if not details:
		details.append("limited tier pricing evidence")

	return _clamp01(score), ", ".join(details)


def _score_segment_coverage(plans: list[dict[str, Any]], pricing_summary: dict[str, Any]) -> tuple[float, str]:
	score = 0.0
	details: list[str] = []
	plan_count = len(plans)

	if plan_count >= 4:
		score += 0.50
		details.append(f"{plan_count} plans")
	elif plan_count >= 3:
		score += 0.32
		details.append(f"{plan_count} plans")
	elif plan_count >= 2:
		score += 0.18
		details.append(f"{plan_count} plans")

	if pricing_summary.get("enterprise_tier"):
		score += 0.35
		details.append("enterprise tier")

	if pricing_summary.get("free_tier"):
		score += 0.15
		details.append("free tier")

	if not details:
		details.append("weak segment coverage signal")

	return _clamp01(score), ", ".join(details)


def _score_feature_depth(plans: list[dict[str, Any]]) -> tuple[float, str, float, int]:
	if not plans:
		return 0.0, "no plan features extracted", 0.0, 0

	feature_lists = [plan.get("features", []) for plan in plans]
	feature_counts = [len(features) for features in feature_lists]
	avg_features = mean(feature_counts) if feature_counts else 0.0

	unique_features = {
		feature.strip().lower()
		for features in feature_lists
		for feature in features
		if feature and len(feature.strip()) > 2
	}
	unique_count = len(unique_features)

	# Blend density and diversity.
	density_score = _clamp01(avg_features / 6.0)
	diversity_score = _clamp01(unique_count / 20.0)
	score = _clamp01((density_score * 0.55) + (diversity_score * 0.45))
	reasoning = f"avg_features_per_plan={avg_features:.2f}, unique_features={unique_count}"
	return score, reasoning, avg_features, unique_count


def _score_strategic_signals(signal_counts: dict[str, int]) -> tuple[float, str]:
	total_hits = sum(signal_counts.values())
	active_categories = sum(1 for count in signal_counts.values() if count > 0)

	# Reward both breadth (categories) and intensity (hits).
	breadth = _clamp01(active_categories / max(1, len(signal_counts)))
	intensity = _clamp01(total_hits / 12.0)
	score = _clamp01((breadth * 0.6) + (intensity * 0.4))

	reasoning = f"signal_hits={total_hits}, active_signal_categories={active_categories}"
	return score, reasoning


def _score_business_model_pressure(profile: dict[str, Any], numeric_prices: list[float]) -> tuple[float, str]:
	if profile.get("pricing_model") == "transaction_based":
		return 1.0, "transaction-based model can undercut fixed tiers"

	if not numeric_prices:
		return 0.25, "unknown model due to sparse numeric pricing"

	# Fixed tiers are still pressure but lower than transaction/usage models.
	return 0.45, "fixed-tier model with visible price ladder"


def _compute_confidence(profile: dict[str, Any], plans: list[dict[str, Any]], numeric_prices: list[float]) -> float:
	raw_chars = profile.get("raw_char_count", 0)
	text_quality = _clamp01(raw_chars / 8000.0)
	structure_quality = _clamp01(len(plans) / 4.0)
	price_quality = _clamp01(len(numeric_prices) / 4.0)

	return round(_clamp01((text_quality * 0.4) + (structure_quality * 0.35) + (price_quality * 0.25)), 3)


def analyze_profile(profile: dict[str, Any]) -> VulnerabilityResult:
	"""Return an explainable vulnerability score for a single competitor."""
	company = profile.get("company", "Unknown")
	plans = profile.get("plans", [])
	pricing_summary = profile.get("pricing_summary", {})

	numeric_prices = sorted(
		price for price in (_parse_price(plan.get("price")) for plan in plans) if price is not None
	)
	signal_counts = _extract_signal_counts(plans)

	pricing_score, pricing_reason = _score_pricing_pressure(pricing_summary, numeric_prices)
	coverage_score, coverage_reason = _score_segment_coverage(plans, pricing_summary)
	feature_score, feature_reason, avg_features, unique_features = _score_feature_depth(plans)
	strategic_score, strategic_reason = _score_strategic_signals(signal_counts)
	model_score, model_reason = _score_business_model_pressure(profile, numeric_prices)

	component_map = {
		"pricing_pressure": (pricing_score, pricing_reason),
		"segment_coverage": (coverage_score, coverage_reason),
		"feature_depth": (feature_score, feature_reason),
		"strategic_signals": (strategic_score, strategic_reason),
		"business_model_pressure": (model_score, model_reason),
	}

	components: list[ScoreComponent] = []
	weighted_total = 0.0
	for name, weight in _COMPONENT_WEIGHTS.items():
		score, reason = component_map[name]
		weighted_score = round(score * weight, 4)
		weighted_total += weighted_score
		components.append(
			ScoreComponent(
				name=name,
				weight=weight,
				score=round(score, 3),
				weighted_score=weighted_score,
				reasoning=reason,
			)
		)

	vulnerability_score = round(_clamp01(weighted_total), 3)
	confidence = _compute_confidence(profile, plans, numeric_prices)
	risk_level = _bucket(vulnerability_score)

	decision_trace = [
		f"pricing_summary.free_tier={pricing_summary.get('free_tier', False)}",
		f"pricing_summary.enterprise_tier={pricing_summary.get('enterprise_tier', False)}",
		f"plan_count={len(plans)}",
		f"numeric_prices={numeric_prices}",
		f"signal_counts={signal_counts}",
		f"weighted_total_before_peer_adjustment={vulnerability_score:.3f}",
	]

	detailed_reasoning = [
		f"{component.name}: score={component.score:.3f}, weight={component.weight:.2f}, "
		f"contribution={component.weighted_score:.3f} ({component.reasoning})"
		for component in components
	]
	detailed_reasoning.append(
		f"confidence={confidence:.3f} based on raw_char_count={profile.get('raw_char_count', 0)}, "
		f"plans={len(plans)}, numeric_prices={len(numeric_prices)}"
	)

	top_component = max(components, key=lambda c: c.weighted_score)
	reasoning_summary = (
		f"Top driver: {top_component.name} ({top_component.weighted_score:.3f}). "
		f"Overall vulnerability={vulnerability_score:.3f} ({risk_level})."
	)

	metrics = {
		"plan_count": len(plans),
		"price_range": pricing_summary.get("price_range", "N/A"),
		"raw_char_count": profile.get("raw_char_count", 0),
		"avg_features_per_plan": round(avg_features, 3),
		"unique_feature_count": unique_features,
		"numeric_price_count": len(numeric_prices),
	}

	return VulnerabilityResult(
		company=company,
		vulnerability_score=vulnerability_score,
		risk_level=risk_level,
		confidence=confidence,
		reasoning_summary=reasoning_summary,
		detailed_reasoning=detailed_reasoning,
		decision_trace=decision_trace,
		component_breakdown=components,
		signals=signal_counts,
		metrics=metrics,
		scraped_at=profile.get("scraped_at", datetime.now(timezone.utc).isoformat()),
		peer_rank=None,
		peer_percentile=None,
	)


def analyze_profiles(profiles: list[dict[str, Any]]) -> list[VulnerabilityResult]:
	"""Analyze all profiles, then add peer-relative adjustment and ranking."""
	results = [analyze_profile(profile) for profile in profiles]
	if not results:
		return []

	# Peer-relative calibration improves separation when baseline scores are close.
	feature_values = [r.metrics.get("avg_features_per_plan", 0.0) for r in results]
	plan_values = [r.metrics.get("plan_count", 0) for r in results]
	signal_values = [sum(r.signals.values()) for r in results]
	base_values = [r.vulnerability_score for r in results]

	def _norm(value: float, values: list[float]) -> float:
		lo = min(values)
		hi = max(values)
		if hi == lo:
			return 0.5
		return (value - lo) / (hi - lo)

	for result in results:
		feature_norm = _norm(result.metrics.get("avg_features_per_plan", 0.0), feature_values)
		plan_norm = _norm(float(result.metrics.get("plan_count", 0)), [float(v) for v in plan_values])
		signal_norm = _norm(float(sum(result.signals.values())), [float(v) for v in signal_values])
		base_norm = _norm(result.vulnerability_score, base_values)

		peer_pressure = _clamp01(
			(feature_norm * 0.30)
			+ (plan_norm * 0.25)
			+ (signal_norm * 0.30)
			+ (base_norm * 0.15)
		)

		peer_adjustment = (peer_pressure - 0.5) * 0.16
		adjusted_score = _clamp01(result.vulnerability_score + peer_adjustment)
		result.decision_trace.append(
			"peer_adjustment="
			f"{peer_adjustment:+.3f} from peer_pressure={peer_pressure:.3f} "
			f"(feature_norm={feature_norm:.3f}, plan_norm={plan_norm:.3f}, "
			f"signal_norm={signal_norm:.3f}, base_norm={base_norm:.3f})"
		)
		result.vulnerability_score = round(adjusted_score, 3)
		result.risk_level = _bucket(result.vulnerability_score)

	ranked = sorted(results, key=lambda item: item.vulnerability_score, reverse=True)
	total = len(ranked)
	for index, result in enumerate(ranked, start=1):
		result.peer_rank = index
		if total == 1:
			result.peer_percentile = 1.0
		else:
			result.peer_percentile = round(1 - ((index - 1) / (total - 1)), 3)
		result.reasoning_summary = (
			f"Ranked #{result.peer_rank}/{total} (peer_percentile={result.peer_percentile:.3f}). "
			f"{result.reasoning_summary}"
		)

	return ranked


def save_vulnerability_report(results: list[VulnerabilityResult], output_dir: str | Path) -> Path:
	output_dir = Path(output_dir)
	output_dir.mkdir(parents=True, exist_ok=True)
	out_path = output_dir / "vulnerability_report.json"

	payload = {
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"model": "weighted_explainable_v1",
		"weights": _COMPONENT_WEIGHTS,
		"results": [asdict(result) for result in results],
	}
	with open(out_path, "w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2, ensure_ascii=False)
	return out_path


def print_vulnerability_report(results: list[VulnerabilityResult]) -> None:
	print(f"\n{'=' * 96}")
	print(f"{'COMPETITIVE VULNERABILITY ANALYSIS (EXPLAINABLE)':^96}")
	print(f"{'=' * 96}")

	for result in results:
		print(
			f"\n[{result.company}] score={result.vulnerability_score:.3f} "
			f"risk={result.risk_level.upper()} confidence={result.confidence:.3f} "
			f"rank={result.peer_rank}/{len(results)}"
		)
		print(f"Summary: {result.reasoning_summary}")
		print("Component breakdown:")
		for component in result.component_breakdown:
			print(
				f"  - {component.name:<24} score={component.score:.3f} "
				f"weight={component.weight:.2f} contribution={component.weighted_score:.3f}"
			)
			print(f"    reasoning: {component.reasoning}")

		print("Detailed reasoning:")
		for line in result.detailed_reasoning:
			print(f"  - {line}")

		print("Decision trace:")
		for step in result.decision_trace:
			print(f"  - {step}")

	print(f"\n{'=' * 96}\n")
