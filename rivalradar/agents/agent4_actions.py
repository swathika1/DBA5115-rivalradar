"""Agent 4: portfolio action recommendations with decision trace."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass
class ActionRecommendation:
	company: str
	priority: str
	recommendation_type: str
	owner: str
	due_window: str
	action_title: str
	action_detail: str
	rationale: str
	evidence: dict[str, Any]
	decision_trace: list[str]
	generated_at: str


def _priority(score: float) -> str:
	if score >= 0.80:
		return "P0"
	if score >= 0.65:
		return "P1"
	if score >= 0.50:
		return "P2"
	return "P3"


def _due_window(priority: str) -> str:
	if priority == "P0":
		return "48 hours"
	if priority == "P1":
		return "7 days"
	if priority == "P2":
		return "14 days"
	return "30 days"


def _owner_for_action(recommendation_type: str) -> str:
	mapping = {
		"pricing_response": "Portfolio Operations Lead",
		"product_response": "Product Advisor / CTO Partner",
		"gtm_response": "GTM Advisor",
		"monitor_only": "Analyst",
	}
	return mapping.get(recommendation_type, "Portfolio Operations Lead")


def _classify_action(vulnerability_score: float, change_probability: float, signal_hits: int) -> str:
	if change_probability >= 0.78:
		return "pricing_response"
	if vulnerability_score >= 0.70 and signal_hits >= 6:
		return "product_response"
	if vulnerability_score >= 0.60:
		return "gtm_response"
	return "monitor_only"


def _build_action_detail(recommendation_type: str, company: str, timeline: str) -> tuple[str, str]:
	if recommendation_type == "pricing_response":
		return (
			f"Run pricing defense sprint against {company}",
			(
				"Convene pricing council, map competitor tier overlap, and model three response "
				f"options (discount fence, packaging shift, value-add bundle) before {timeline}."
			),
		)
	if recommendation_type == "product_response":
		return (
			f"Launch feature-gap closure plan for {company}",
			(
				"Escalate top 3 feature gaps to portfolio CTO and define a 30-60 day roadmap patch "
				"with explicit customer retention targets."
			),
		)
	if recommendation_type == "gtm_response":
		return (
			f"Prepare GTM counter-messaging against {company}",
			(
				"Arm sales and customer success with objection-handling for likely pricing/features moves "
				"and deploy retention outreach to at-risk segments."
			),
		)
	return (
		f"Continue structured monitoring for {company}",
		"No immediate intervention needed. Keep weekly watchlist tracking active and auto-alert on score jumps.",
	)


def generate_action_recommendations(
	vulnerability_results: list[Any],
	pricing_predictions: list[Any],
) -> list[ActionRecommendation]:
	"""Generate VC-facing action recommendations from Agent 2 + Agent 3 outputs."""
	by_company_prediction = {item.company: item for item in pricing_predictions}
	recommendations: list[ActionRecommendation] = []

	for vuln in vulnerability_results:
		company = getattr(vuln, "company", "Unknown")
		prediction = by_company_prediction.get(company)
		if prediction is None:
			continue

		vulnerability_score = float(getattr(vuln, "vulnerability_score", 0.0))
		change_probability = float(getattr(prediction, "change_probability", 0.0))
		confidence = float(getattr(vuln, "confidence", 0.5))
		signal_hits = int(sum(getattr(vuln, "signals", {}).values()))

		decision_score = (
			vulnerability_score * 0.46
			+ change_probability * 0.42
			+ confidence * 0.12
		)
		decision_score = round(max(0.0, min(1.0, decision_score)), 3)

		recommendation_type = _classify_action(vulnerability_score, change_probability, signal_hits)
		priority = _priority(decision_score)
		due_window = _due_window(priority)
		owner = _owner_for_action(recommendation_type)
		title, detail = _build_action_detail(
			recommendation_type,
			company,
			prediction.predicted_timeline,
		)

		rationale = (
			f"{company} is {getattr(vuln, 'risk_level', 'unknown')} risk with vulnerability "
			f"score {vulnerability_score:.3f}; predicted pricing change probability is "
			f"{change_probability:.3f} ({prediction.predicted_timeline})."
		)

		evidence = {
			"vulnerability_score": vulnerability_score,
			"vulnerability_rank": getattr(vuln, "peer_rank", None),
			"pricing_change_probability": change_probability,
			"predicted_timeline": prediction.predicted_timeline,
			"signal_hits": signal_hits,
			"price_range": getattr(vuln, "metrics", {}).get("price_range", "N/A"),
		}

		decision_trace = [
			f"input.vulnerability_score={vulnerability_score:.3f}",
			f"input.change_probability={change_probability:.3f}",
			f"input.confidence={confidence:.3f}",
			f"input.signal_hits={signal_hits}",
			"decision_score="
			f"0.46*{vulnerability_score:.3f} + 0.42*{change_probability:.3f} + 0.12*{confidence:.3f}",
			f"output.decision_score={decision_score:.3f}",
			f"output.recommendation_type={recommendation_type}",
			f"output.priority={priority}",
			f"output.owner={owner}",
			f"output.due_window={due_window}",
		]

		recommendations.append(
			ActionRecommendation(
				company=company,
				priority=priority,
				recommendation_type=recommendation_type,
				owner=owner,
				due_window=due_window,
				action_title=title,
				action_detail=detail,
				rationale=rationale,
				evidence=evidence,
				decision_trace=decision_trace,
				generated_at=datetime.now(timezone.utc).isoformat(),
			)
		)

	priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
	return sorted(
		recommendations,
		key=lambda item: (priority_order.get(item.priority, 9), item.company),
	)


def save_action_recommendations(
	recommendations: list[ActionRecommendation],
	output_dir: str | Path,
) -> Path:
	output_dir = Path(output_dir)
	output_dir.mkdir(parents=True, exist_ok=True)
	out_path = output_dir / "action_recommendations_report.json"

	payload = {
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"model": "action_recommendation_explainable_v1",
		"results": [asdict(item) for item in recommendations],
	}
	with open(out_path, "w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2, ensure_ascii=False)
	return out_path


def print_action_recommendations(recommendations: list[ActionRecommendation]) -> None:
	print(f"\n{'=' * 96}")
	print(f"{'AGENT 4: VC ACTION RECOMMENDATIONS':^96}")
	print(f"{'=' * 96}")

	for recommendation in recommendations:
		print(
			f"\n[{recommendation.company}] {recommendation.priority} | "
			f"{recommendation.recommendation_type} | due={recommendation.due_window}"
		)
		print(f"Owner: {recommendation.owner}")
		print(f"Action: {recommendation.action_title}")
		print(f"Detail: {recommendation.action_detail}")
		print(f"Rationale: {recommendation.rationale}")
		print("Evidence:")
		for key, value in recommendation.evidence.items():
			print(f"  - {key}: {value}")
		print("Decision trace:")
		for step in recommendation.decision_trace:
			print(f"  - {step}")

	print(f"\n{'=' * 96}\n")
