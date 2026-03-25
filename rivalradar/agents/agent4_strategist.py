import os
import logging
from enum import Enum
from groq import Groq
from agents import chat_json, LLMParseError

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    ACQUISITION = "acquisition_target"
    PIVOT = "product_pivot"
    PRICING = "pricing_defense"
    PARTNERSHIP = "partnership_acceleration"
    MONITOR = "monitor_only"


_VALID_RT = {e.value for e in RecommendationType}

SYSTEM_PROMPT = """You are a board-level strategic advisor for a VC firm.
Given risk assessments and impact forecasts, return a JSON array of ActionRecommendation objects.
Each object must have:
  company (str), priority (one of: P0/P1/P2/P3), recommendation_type (one of: acquisition_target/product_pivot/pricing_defense/partnership_acceleration/monitor_only),
  owner (board-level role str), due_window (str), action_title (str), action_detail (str),
  rationale (str), evidence (dict), decision_trace (list of str), generated_at (ISO string).
All recommendations must be framed as board-meeting directives, never product feature requests.
Return ONLY valid JSON, no markdown."""


class Agent4:
    """Strategist Agent - Generates strategic recommendations for the board."""
    
    def __init__(self, client=None):
        self.client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))

    def strategize(self, agent2_output: list[dict], agent3_output: list[dict]) -> list[dict]:
        """Generate strategic recommendations."""
        results = []
        for assessment in agent2_output:
            company = assessment.get("company", "Unknown")
            forecast = next((f for f in agent3_output if f.get("company") == company), {})
            try:
                raw = chat_json(
                    self.client,
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Assessment: {assessment}\nForecast: {forecast}"},
                    ],
                    temperature=0.4,
                    max_retries=1,
                )
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    rt = item.get("recommendation_type")
                    if rt not in _VALID_RT:
                        raise LLMParseError(f"Invalid recommendation_type: {rt!r}")
                    results.append(item)
            except LLMParseError as exc:
                logger.error("Agent4 skipping %s: %s", company, exc)
        return results
