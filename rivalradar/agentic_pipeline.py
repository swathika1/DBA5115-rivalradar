"""
RivalRadar Agentic Pipeline - 4 Agent System
Agents: 1) Collector, 2) Vulnerability Analyzer, 3) Pricing Predictor, 4) Action Planner
"""

import asyncio
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from openai import OpenAI

from competitor_targets import COMPETITOR_TARGETS
from scrapers.output_parser import parse_pricing_page, save_structured

# Crawlee is optional for live scraping; fallback mode can still run without it.
try:
    from scrapers.crawlee_scraper import CrawleeScraper
    CRAWLEE_AVAILABLE = True
except ModuleNotFoundError:
    CrawleeScraper = None
    CRAWLEE_AVAILABLE = False

OUTPUT_DIR = Path("scraper_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────────────────
# API Key Loading
# ────────────────────────────────────────────────────────────────────────────

def _load_env_file(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

_env = _load_env_file(Path(".env"))
if not _env:
    _env = _load_env_file(Path(".env.example"))

OPENAI_API_KEY = _env.get("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = _env.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_MODEL = _env.get("OPENAI_MODEL", "gpt-4o-mini")

RUN_LIVE_SCRAPE = CRAWLEE_AVAILABLE
VERBOSE = True
MAX_RETRIES = 1


def get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env or .env.example")
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def chat_json(client: OpenAI, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI returned empty content")
    return json.loads(content)


# ────────────────────────────────────────────────────────────────────────────
# Agent 1: Collector
# ────────────────────────────────────────────────────────────────────────────

class Agent1Collector:
    """Collect competitor pricing pages and emit structured competitor profiles."""

    def __init__(self, output_dir: Path, companies: list[dict[str, str]] | None = None):
        self.output_dir = output_dir
        self.companies = companies if companies else COMPETITOR_TARGETS
        self.scraper = CrawleeScraper() if CRAWLEE_AVAILABLE else None

    def build_targets(self) -> list[dict[str, str]]:
        return [
            {
                "url": target["pricing_url"],
                "page_type": "pricing",
                "name": target["name"],
            }
            for target in self.companies
        ]

    async def collect(self) -> dict[str, Any]:
        if self.scraper is None:
            raise ModuleNotFoundError(
                "crawlee is not installed. Install deps with: pip install -r requirements.txt"
            )

        targets = self.build_targets()
        scrape_results = await self.scraper.scrape_pages(targets)

        profiles: list[dict[str, Any]] = []
        for result in scrape_results:
            profile = parse_pricing_page(
                raw_text=result.get("raw_text", ""),
                company=result.get("name", "Unknown"),
                url=result.get("url", ""),
                scraped_at=result.get("scraped_at", ""),
            )
            save_structured(profile, self.output_dir)
            profiles.append(profile)

        return {
            "agent": "agent1_collector",
            "target_count": len(targets),
            "scrape_result_count": len(scrape_results),
            "structured_profiles": profiles,
        }


def load_existing_structured_profiles(output_dir: Path) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for path in sorted(output_dir.glob("*_structured.json")):
        with open(path, encoding="utf-8") as f:
            profiles.append(json.load(f))
    return profiles


# ────────────────────────────────────────────────────────────────────────────
# Agent 2: Vulnerability Analyzer
# ────────────────────────────────────────────────────────────────────────────

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


class Agent2CompetitiveAnalyzer:
    """Analyze competitor profiles with OpenAI and return explainable vulnerability results."""

    component_weights = {
        "pricing_pressure": 0.28,
        "segment_coverage": 0.22,
        "feature_depth": 0.18,
        "strategic_signals": 0.20,
        "business_model_pressure": 0.12,
    }

    def __init__(self, output_dir: Path, client: OpenAI):
        self.output_dir = output_dir
        self.client = client

    def _analyze_one(self, profile: dict[str, Any]) -> VulnerabilityResult:
        prompt = (
            "You are a senior competitive intelligence analyst. Return strict JSON only. "
            "Analyze this competitor profile and produce vulnerability analysis.\n"
            "Required keys: vulnerability_score, confidence, risk_level, reasoning_summary, "
            "detailed_reasoning, decision_trace, component_breakdown, signals, metrics.\n"
            "component_breakdown must include these names exactly: pricing_pressure, segment_coverage, "
            "feature_depth, strategic_signals, business_model_pressure.\n"
            "signals must include ai_momentum, enterprise_readiness, integration_strength as integers.\n"
            f"Profile: {json.dumps(profile, ensure_ascii=False)}"
        )
        payload = chat_json(
            self.client,
            "Return only valid JSON, no markdown.",
            prompt,
            temperature=0.1,
        )

        components_by_name = {
            item.get("name", "").lower().strip().replace(" ", "_"): item
            for item in payload.get("component_breakdown", [])
            if isinstance(item, dict)
        }

        components: list[ScoreComponent] = []
        for name, weight in self.component_weights.items():
            raw = components_by_name.get(name, {})
            score = max(0.0, min(1.0, float(raw.get("score", 0.0))))
            components.append(
                ScoreComponent(
                    name=name,
                    weight=weight,
                    score=round(score, 3),
                    weighted_score=round(score * weight, 4),
                    reasoning=str(raw.get("reasoning", "No reasoning provided.")).strip(),
                )
            )

        vulnerability_score = max(0.0, min(1.0, float(payload.get("vulnerability_score", sum(c.weighted_score for c in components)))))
        confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.6))))
        risk_level = str(payload.get("risk_level", "medium")).lower().strip()
        if risk_level not in {"low", "medium", "high", "critical"}:
            risk_level = "high" if vulnerability_score >= 0.65 else ("medium" if vulnerability_score >= 0.45 else "low")

        signals_raw = payload.get("signals", {}) if isinstance(payload.get("signals"), dict) else {}
        signals = {
            "ai_momentum": int(signals_raw.get("ai_momentum", 0)),
            "enterprise_readiness": int(signals_raw.get("enterprise_readiness", 0)),
            "integration_strength": int(signals_raw.get("integration_strength", 0)),
        }

        metrics_raw = payload.get("metrics", {}) if isinstance(payload.get("metrics"), dict) else {}
        metrics = {
            "plan_count": int(metrics_raw.get("plan_count", len(profile.get("plans", [])))),
            "price_range": metrics_raw.get("price_range", profile.get("pricing_summary", {}).get("price_range", "N/A")),
            "raw_char_count": int(metrics_raw.get("raw_char_count", profile.get("raw_char_count", 0))),
            "avg_features_per_plan": float(metrics_raw.get("avg_features_per_plan", 0.0)),
            "unique_feature_count": int(metrics_raw.get("unique_feature_count", 0)),
            "numeric_price_count": int(metrics_raw.get("numeric_price_count", 0)),
        }

        detailed_reasoning = payload.get("detailed_reasoning", [])
        if not isinstance(detailed_reasoning, list):
            detailed_reasoning = [str(detailed_reasoning)]

        decision_trace = payload.get("decision_trace", [])
        if not isinstance(decision_trace, list):
            decision_trace = [str(decision_trace)]

        return VulnerabilityResult(
            company=profile.get("company", "Unknown"),
            vulnerability_score=round(vulnerability_score, 3),
            risk_level=risk_level,
            confidence=round(confidence, 3),
            reasoning_summary=str(payload.get("reasoning_summary", "No summary provided.")).strip(),
            detailed_reasoning=[str(x) for x in detailed_reasoning],
            decision_trace=[str(x) for x in decision_trace],
            component_breakdown=components,
            signals=signals,
            metrics=metrics,
            scraped_at=profile.get("scraped_at", datetime.now(timezone.utc).isoformat()),
            peer_rank=None,
            peer_percentile=None,
        )

    def analyze(self, agent1_output: dict[str, Any]) -> dict[str, Any]:
        profiles = agent1_output["structured_profiles"]
        results = [self._analyze_one(profile) for profile in profiles]
        results.sort(key=lambda r: r.vulnerability_score, reverse=True)

        total = len(results)
        for idx, result in enumerate(results, start=1):
            result.peer_rank = idx
            result.peer_percentile = 1.0 if total == 1 else round(1 - ((idx - 1) / (total - 1)), 3)
            result.reasoning_summary = (
                f"Ranked #{result.peer_rank}/{total} (peer_percentile={result.peer_percentile:.3f}). "
                f"{result.reasoning_summary}"
            )

        report_path = self.output_dir / "vulnerability_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": "openai_vulnerability_v1",
                    "results": [asdict(r) for r in results],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return {
            "agent": "agent2_analyzer",
            "vulnerability_results": results,
            "report_path": str(report_path),
            "analyzed_count": len(results),
        }


# ────────────────────────────────────────────────────────────────────────────
# Agent 3: Pricing Predictor
# ────────────────────────────────────────────────────────────────────────────

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


class Agent3PricingPredictor:
    """Predict competitor pricing-change likelihood and timeline using OpenAI."""

    def __init__(self, output_dir: Path, client: OpenAI):
        self.output_dir = output_dir
        self.client = client

    def _predict_one(self, vuln: VulnerabilityResult, profile: dict[str, Any]) -> PricingPrediction:
        context = {
            "company": vuln.company,
            "vulnerability_score": vuln.vulnerability_score,
            "risk_level": vuln.risk_level,
            "confidence": vuln.confidence,
            "signals": vuln.signals,
            "metrics": vuln.metrics,
            "profile": profile,
        }
        prompt = (
            "Predict pricing change likelihood and timeline. Return strict JSON only.\n"
            "Required keys: change_probability, predicted_timeline, risk_level, reasoning_summary, drivers, decision_trace, evidence.\n"
            "risk_level must be low/medium/high.\n"
            "predicted_timeline must be one of: 0-30 days, 1-2 months, 2-3 months, 3+ months.\n"
            "drivers must include: vulnerability_pressure, strategic_signal_intensity, plan_complexity, "
            "portfolio_competition_intensity, pricing_plan_volatility, analysis_confidence with [0,1] floats.\n"
            f"Context: {json.dumps(context, ensure_ascii=False)}"
        )

        payload = chat_json(self.client, "Return only valid JSON.", prompt, temperature=0.15)
        probability = max(0.0, min(1.0, float(payload.get("change_probability", 0.0))))
        risk = str(payload.get("risk_level", "low")).lower().strip()
        if risk not in {"low", "medium", "high"}:
            risk = "high" if probability >= 0.75 else ("medium" if probability >= 0.5 else "low")

        timeline = str(payload.get("predicted_timeline", "3+ months")).strip()
        if timeline not in {"0-30 days", "1-2 months", "2-3 months", "3+ months"}:
            timeline = "0-30 days" if probability >= 0.8 else ("1-2 months" if probability >= 0.65 else ("2-3 months" if probability >= 0.5 else "3+ months"))

        raw_drivers = payload.get("drivers", {}) if isinstance(payload.get("drivers"), dict) else {}
        drivers = {
            "vulnerability_pressure": round(max(0.0, min(1.0, float(raw_drivers.get("vulnerability_pressure", vuln.vulnerability_score)))), 3),
            "strategic_signal_intensity": round(max(0.0, min(1.0, float(raw_drivers.get("strategic_signal_intensity", 0.0)))), 3),
            "plan_complexity": round(max(0.0, min(1.0, float(raw_drivers.get("plan_complexity", 0.0)))), 3),
            "portfolio_competition_intensity": round(max(0.0, min(1.0, float(raw_drivers.get("portfolio_competition_intensity", 0.0)))), 3),
            "pricing_plan_volatility": round(max(0.0, min(1.0, float(raw_drivers.get("pricing_plan_volatility", 0.0)))), 3),
            "analysis_confidence": round(max(0.0, min(1.0, float(raw_drivers.get("analysis_confidence", vuln.confidence)))), 3),
        }

        decision_trace = payload.get("decision_trace", [])
        if not isinstance(decision_trace, list):
            decision_trace = [str(decision_trace)]

        evidence = payload.get("evidence", {}) if isinstance(payload.get("evidence"), dict) else {}
        evidence.setdefault("price_range", vuln.metrics.get("price_range", "N/A"))
        evidence.setdefault("peer_rank", vuln.peer_rank)

        return PricingPrediction(
            company=vuln.company,
            change_probability=round(probability, 3),
            predicted_timeline=timeline,
            risk_level=risk,
            reasoning_summary=str(payload.get("reasoning_summary", "No summary provided.")).strip(),
            drivers=drivers,
            decision_trace=[str(x) for x in decision_trace],
            evidence=evidence,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, agent1_output: dict[str, Any], agent2_output: dict[str, Any]) -> dict[str, Any]:
        profiles = {p.get("company", "Unknown"): p for p in agent1_output["structured_profiles"]}
        vulnerability_results = agent2_output["vulnerability_results"]

        predictions = [
            self._predict_one(vuln, profiles.get(vuln.company, {}))
            for vuln in vulnerability_results
        ]
        predictions.sort(key=lambda p: p.change_probability, reverse=True)

        report_path = self.output_dir / "pricing_predictions_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": "openai_pricing_prediction_v1",
                    "results": [asdict(p) for p in predictions],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return {
            "agent": "agent3_pricing",
            "pricing_predictions": predictions,
            "report_path": str(report_path),
            "prediction_count": len(predictions),
        }


# ────────────────────────────────────────────────────────────────────────────
# Agent 4: Action Planner
# ────────────────────────────────────────────────────────────────────────────

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


class Agent4ActionPlanner:
    """Generate VC-facing action recommendations from Agent 2 + Agent 3 with OpenAI."""

    def __init__(self, output_dir: Path, client: OpenAI):
        self.output_dir = output_dir
        self.client = client

    def _recommend_one(self, vuln: VulnerabilityResult, pred: PricingPrediction) -> ActionRecommendation:
        context = {
            "company": vuln.company,
            "vulnerability_score": vuln.vulnerability_score,
            "vulnerability_risk": vuln.risk_level,
            "vulnerability_summary": vuln.reasoning_summary,
            "pricing_change_probability": pred.change_probability,
            "pricing_timeline": pred.predicted_timeline,
            "pricing_risk": pred.risk_level,
            "pricing_summary": pred.reasoning_summary,
        }
        prompt = (
            "Generate one VC action recommendation. Return strict JSON only.\n"
            "Required keys: priority, recommendation_type, owner, due_window, action_title, action_detail, rationale, evidence, decision_trace.\n"
            "priority must be one of: P0, P1, P2, P3.\n"
            "recommendation_type must be one of: pricing_response, product_response, gtm_response, monitor_only.\n"
            f"Context: {json.dumps(context, ensure_ascii=False)}"
        )

        payload = chat_json(self.client, "Return only valid JSON.", prompt, temperature=0.2)
        priority = str(payload.get("priority", "P2")).upper().strip()
        if priority not in {"P0", "P1", "P2", "P3"}:
            priority = "P2"

        rec_type = str(payload.get("recommendation_type", "monitor_only")).lower().strip()
        if rec_type not in {"pricing_response", "product_response", "gtm_response", "monitor_only"}:
            rec_type = "monitor_only"

        decision_trace = payload.get("decision_trace", [])
        if not isinstance(decision_trace, list):
            decision_trace = [str(decision_trace)]

        evidence = payload.get("evidence", {}) if isinstance(payload.get("evidence"), dict) else {}
        evidence.setdefault("vulnerability_score", vuln.vulnerability_score)
        evidence.setdefault("pricing_change_probability", pred.change_probability)

        return ActionRecommendation(
            company=vuln.company,
            priority=priority,
            recommendation_type=rec_type,
            owner=str(payload.get("owner", "Portfolio Operations Lead")).strip(),
            due_window=str(payload.get("due_window", "14 days")).strip(),
            action_title=str(payload.get("action_title", f"Monitor {vuln.company}")).strip(),
            action_detail=str(payload.get("action_detail", "No detail provided.")).strip(),
            rationale=str(payload.get("rationale", "No rationale provided.")).strip(),
            evidence=evidence,
            decision_trace=[str(x) for x in decision_trace],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def recommend(self, agent2_output: dict[str, Any], agent3_output: dict[str, Any]) -> dict[str, Any]:
        vulnerability_results = agent2_output["vulnerability_results"]
        predictions = {p.company: p for p in agent3_output["pricing_predictions"]}

        recommendations: list[ActionRecommendation] = []
        for vuln in vulnerability_results:
            pred = predictions.get(vuln.company)
            if pred is None:
                continue
            recommendations.append(self._recommend_one(vuln, pred))

        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        recommendations.sort(key=lambda r: (priority_order.get(r.priority, 9), r.company))

        report_path = self.output_dir / "action_recommendations_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": "openai_action_recommendation_v1",
                    "results": [asdict(r) for r in recommendations],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return {
            "agent": "agent4_actions",
            "action_recommendations": recommendations,
            "report_path": str(report_path),
            "recommendation_count": len(recommendations),
        }


# ────────────────────────────────────────────────────────────────────────────
# Pipeline Orchestrator
# ────────────────────────────────────────────────────────────────────────────

async def run_agent_pipeline(run_live_scrape: bool = True, companies: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Execute all 4 agents in sequence
    
    Args:
        run_live_scrape: Whether to scrape live or use cached data
        companies: List of company dicts with name, domain, pricing_url, page_types, market_segment
                  If None, uses COMPETITOR_TARGETS from competitor_targets.py
    """
    start = time.perf_counter()

    # Use provided companies or default to hardcoded
    companies_to_process = companies if companies else COMPETITOR_TARGETS

    client = get_openai_client()

    agent1 = Agent1Collector(OUTPUT_DIR, companies_to_process)
    agent2 = Agent2CompetitiveAnalyzer(OUTPUT_DIR, client)
    agent3 = Agent3PricingPredictor(OUTPUT_DIR, client)
    agent4 = Agent4ActionPlanner(OUTPUT_DIR, client)

    agent1_output: dict[str, Any] | None = None

    if run_live_scrape:
        for attempt in range(MAX_RETRIES + 1):
            try:
                if VERBOSE:
                    print(f"[Agent1] Live scrape attempt {attempt + 1}/{MAX_RETRIES + 1}")
                agent1_output = await agent1.collect()
                if VERBOSE:
                    print(f"[Agent1] Scraped {len(agent1_output.get('structured_profiles', []))} profiles.")
                break
            except Exception as exc:
                print(f"[Agent1] Attempt failed: {exc}")
                if attempt == MAX_RETRIES:
                    print("[Agent1] Falling back to existing structured JSON files.")

    # Fall back if scrape was skipped, failed, or returned no profiles
    if agent1_output is None or len(agent1_output.get("structured_profiles", [])) == 0:
        profiles = load_existing_structured_profiles(OUTPUT_DIR)
        if VERBOSE:
            print(f"[Agent1] Loaded {len(profiles)} existing structured profiles from disk.")
        agent1_output = {
            "agent": "agent1_collector_fallback",
            "target_count": len(companies_to_process),
            "scrape_result_count": 0,
            "structured_profiles": profiles,
        }

    agent2_output = agent2.analyze(agent1_output)
    agent3_output = agent3.predict(agent1_output, agent2_output)
    agent4_output = agent4.recommend(agent2_output, agent3_output)

    elapsed = time.perf_counter() - start
    if VERBOSE:
        print(f"[Pipeline] Completed in {elapsed:.2f}s")

    return {
        "elapsed_seconds": elapsed,
        "agent1_output": agent1_output,
        "agent2_output": agent2_output,
        "agent3_output": agent3_output,
        "agent4_output": agent4_output,
    }
