import os
import logging
from groq import Groq
from agents import chat_json, LLMParseError

logger = logging.getLogger(__name__)

MOAT_DIMENSIONS = [
    ("network_effects", 0.15),
    ("switching_costs", 0.15),
    ("economies_of_scale", 0.10),
    ("proprietary_technology", 0.15),
    ("brand_strength", 0.10),
    ("data_moat", 0.15),
    ("integration_lock_in", 0.10),
    ("regulatory_barriers", 0.10),
]

SYSTEM_PROMPT = """You are a competitive intelligence analyst for a VC portfolio monitoring platform.
Analyse the provided competitor profiles and return a JSON array of PortfolioRiskAssessment objects.
Each object must have exactly these fields:
  company (str), vulnerability_score (float 0-1), risk_level (str: low/medium/high/critical),
  confidence (float 0-1), reasoning_summary (str), detailed_reasoning (list of str),
  decision_trace (list of str), component_breakdown (list of objects with dimension and score),
  signals (dict), metrics (dict), peer_rank (int), peer_percentile (float).
Score each of the 8 moat dimensions: network_effects, switching_costs, economies_of_scale,
proprietary_technology, brand_strength, data_moat, integration_lock_in, regulatory_barriers.
vulnerability_score = weighted average (see weights). Return ONLY valid JSON, no markdown."""


class Agent2:
    """Analyzer Agent - Analyzes competitor profiles for portfolio risk."""
    
    def __init__(self, client=None):
        self.client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))

    def analyze(self, structured_profiles: list[dict]) -> list[dict]:
        """Analyze structured profiles and return risk assessments."""
        results = []
        for profile in structured_profiles:
            try:
                raw = chat_json(
                    self.client,
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyse this competitor: {profile}"},
                    ],
                    temperature=0.2,
                    max_retries=1,
                )
                # raw may be a list or a single dict
                if isinstance(raw, list):
                    results.extend(raw)
                else:
                    results.append(raw)
            except LLMParseError as exc:
                logger.error("Agent2 skipping %s: %s", profile.get("name"), exc)
        return results
