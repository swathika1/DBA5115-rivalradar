"""Agent 3: pricing-change prediction with explainable reasoning."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass
class PricingPrediction:
	company: str
	change_probability: float
	predicted_timeline: str
	risk_level: str
	reasoning_summary: str
	drivers: dict[str, float]
	decision_trace: list[str]
	evidence: dict[str, Any]
	generated_at: str


def _bucket(probability: float) -> str:
	if probability >= 0.78:
		return "high"
	if probability >= 0.55:
		return "medium"
	return "low"


def _timeline(probability: float) -> str:
	if probability >= 0.80:
		return "0-30 days"
	if probability >= 0.65:
		return "1-2 months"
	if probability >= 0.50:
		return "2-3 months"
	return "3+ months"


def _profile_index_by_company(structured_profiles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
	return {profile.get("company", "Unknown"): profile for profile in structured_profiles}


def _numeric_prices(profile: dict[str, Any]) -> list[float]:
	plans = profile.get("plans", [])
	prices: list[float] = []
	for plan in plans:
		price = plan.get("price", "")
		if not isinstance(price, str):
			continue
		if "$" in price:
			cleaned = "".join(ch for ch in price if ch.isdigit() or ch == ".")
			if cleaned:
				try:
					prices.append(float(cleaned))
				except ValueError:
					continue
	return sorted(prices)


def _plan_volatility_signal(profile: dict[str, Any]) -> float:
	plans = profile.get("plans", [])
	if not plans:
		return 0.2

	feature_counts = [len(plan.get("features", [])) for plan in plans]
	spread = max(feature_counts) - min(feature_counts) if feature_counts else 0
	price_points = _numeric_prices(profile)
	price_spread = (max(price_points) - min(price_points)) if len(price_points) >= 2 else 0

	spread_signal = min(1.0, spread / 10.0)
	pricing_signal = min(1.0, price_spread / 30.0)
	return round((spread_signal * 0.55) + (pricing_signal * 0.45), 3)


def _competition_intensity(vulnerability_results: list[Any], current_company: str) -> float:
	others = [r for r in vulnerability_results if getattr(r, "company", "") != current_company]
	if not others:
		return 0.5
	return round(mean(getattr(r, "vulnerability_score", 0.5) for r in others), 3)


def predict_pricing_changes(
	vulnerability_results: list[Any],
	structured_profiles: list[dict[str, Any]],
) -> list[PricingPrediction]:
	"""Predict likelihood of near-term pricing changes per competitor."""
	profile_by_company = _profile_index_by_company(structured_profiles)
	predictions: list[PricingPrediction] = []

	for result in vulnerability_results:
		company = getattr(result, "company", "Unknown")
		profile = profile_by_company.get(company, {})
		metrics = getattr(result, "metrics", {})
		signals = getattr(result, "signals", {})

		vulnerability_score = float(getattr(result, "vulnerability_score", 0.5))
		confidence = float(getattr(result, "confidence", 0.5))
		signal_hits = float(sum(signals.values()))
		signal_intensity = min(1.0, signal_hits / 12.0)
		plan_count = float(metrics.get("plan_count", 0))
		plan_complexity = min(1.0, plan_count / 5.0)
		volatility = _plan_volatility_signal(profile)
		competition = _competition_intensity(vulnerability_results, company)

		drivers = {
			"vulnerability_pressure": round(vulnerability_score, 3),
			"strategic_signal_intensity": round(signal_intensity, 3),
			"plan_complexity": round(plan_complexity, 3),
			"portfolio_competition_intensity": round(competition, 3),
			"pricing_plan_volatility": round(volatility, 3),
			"analysis_confidence": round(confidence, 3),
		}

		probability = (
			drivers["vulnerability_pressure"] * 0.34
			+ drivers["strategic_signal_intensity"] * 0.18
			+ drivers["plan_complexity"] * 0.12
			+ drivers["portfolio_competition_intensity"] * 0.14
			+ drivers["pricing_plan_volatility"] * 0.16
			+ drivers["analysis_confidence"] * 0.06
		)
		probability = round(max(0.0, min(1.0, probability)), 3)

		timeline = _timeline(probability)
		risk = _bucket(probability)

		top_driver_name = max(drivers.items(), key=lambda item: item[1])[0]
		reasoning_summary = (
			f"{company} pricing-change probability={probability:.3f} ({risk}) in {timeline}. "
			f"Top driver: {top_driver_name}."
		)

		decision_trace = [
			f"input.vulnerability_score={vulnerability_score:.3f}",
			f"input.confidence={confidence:.3f}",
			f"input.signal_hits={signal_hits:.0f} -> normalized={signal_intensity:.3f}",
			f"input.plan_count={plan_count:.0f} -> normalized={plan_complexity:.3f}",
			f"input.plan_volatility={volatility:.3f}",
			f"input.peer_competition_intensity={competition:.3f}",
			"weighted_probability="
			f"0.34*{drivers['vulnerability_pressure']:.3f} + "
			f"0.18*{drivers['strategic_signal_intensity']:.3f} + "
			f"0.12*{drivers['plan_complexity']:.3f} + "
			f"0.14*{drivers['portfolio_competition_intensity']:.3f} + "
			f"0.16*{drivers['pricing_plan_volatility']:.3f} + "
			f"0.06*{drivers['analysis_confidence']:.3f}",
			f"output.change_probability={probability:.3f}",
			f"output.timeline={timeline}",
			f"output.risk={risk}",
		]

		evidence = {
			"price_range": metrics.get("price_range", "N/A"),
			"plan_count": int(plan_count),
			"signal_hits": int(signal_hits),
			"peer_rank": getattr(result, "peer_rank", None),
			"peer_percentile": getattr(result, "peer_percentile", None),
		}

		predictions.append(
			PricingPrediction(
				company=company,
				change_probability=probability,
				predicted_timeline=timeline,
				risk_level=risk,
				reasoning_summary=reasoning_summary,
				drivers=drivers,
				decision_trace=decision_trace,
				evidence=evidence,
				generated_at=datetime.now(timezone.utc).isoformat(),
			)
		)

	return sorted(predictions, key=lambda item: item.change_probability, reverse=True)


def save_pricing_predictions(predictions: list[PricingPrediction], output_dir: str | Path) -> Path:
	output_dir = Path(output_dir)
	output_dir.mkdir(parents=True, exist_ok=True)
	out_path = output_dir / "pricing_predictions_report.json"

	payload = {
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"model": "pricing_prediction_explainable_v1",
		"results": [asdict(item) for item in predictions],
	}
	with open(out_path, "w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2, ensure_ascii=False)
	return out_path


def print_pricing_predictions(predictions: list[PricingPrediction]) -> None:
	print(f"\n{'=' * 96}")
	print(f"{'AGENT 3: PRICING CHANGE PREDICTIONS':^96}")
	print(f"{'=' * 96}")

	for prediction in predictions:
		print(
			f"\n[{prediction.company}] probability={prediction.change_probability:.3f} "
			f"risk={prediction.risk_level.upper()} timeline={prediction.predicted_timeline}"
		)
		print(f"Summary: {prediction.reasoning_summary}")
		print("Drivers:")
		for name, value in prediction.drivers.items():
			print(f"  - {name}: {value:.3f}")
		print("Decision trace:")
		for step in prediction.decision_trace:
			print(f"  - {step}")

	print(f"\n{'=' * 96}\n")
