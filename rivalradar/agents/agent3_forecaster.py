import os
import logging
from enum import Enum
from groq import Groq
from agents import chat_json, LLMParseError

logger = logging.getLogger(__name__)


class TimeToImpact(str, Enum):
    SHORT = "0-3 months"
    MEDIUM = "3-6 months"
    LONG = "6-18 months"
    EXTENDED = "18+ months"


_VALID_TTI = {e.value for e in TimeToImpact}

SYSTEM_PROMPT = """You are a financial risk forecaster for a VC portfolio.
Given competitor risk assessments and raw scraped data, return a JSON array of ImpactForecast objects.
Each object must have:
  company (str), revenue_at_risk_pct (float 0-1), time_to_impact (one of: "0-3 months","3-6 months","6-18 months","18+ months"),
  risk_level (str), reasoning_summary (str),
  impact_drivers (dict with keys: moat_weakness, competitive_pressure, market_timing, execution_risk, customer_stickiness, analysis_confidence — all floats 0-1),
  decision_trace (list of str), evidence (dict), generated_at (ISO string).
Return ONLY valid JSON, no markdown."""


class Agent3:
    """Forecaster Agent - Forecasts impact and revenue at risk."""
    
    def __init__(self, client=None):
        self.client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))

    def forecast(self, agent2_output: list[dict], structured_profiles: list[dict]) -> list[dict]:
        """Forecast impact for risk assessments."""
        results = []
        for assessment in agent2_output:
            company = assessment.get("company", "Unknown")
            profile = next((p for p in structured_profiles if p.get("name") == company), {})
            try:
                raw = chat_json(
                    self.client,
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Risk assessment: {assessment}\nRaw profile: {profile}"},
                    ],
                    temperature=0.3,
                    max_retries=1,
                )
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    tti = item.get("time_to_impact")
                    if tti not in _VALID_TTI:
                        raise LLMParseError(f"Invalid time_to_impact value: {tti!r}")
                    results.append(item)
            except LLMParseError as exc:
                logger.error("Agent3 skipping %s: %s", company, exc)
        return results
