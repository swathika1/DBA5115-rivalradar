import json
import logging

logger = logging.getLogger(__name__)


class LLMParseError(Exception):
    pass


def chat_json(client, messages, model="llama-3.3-70b-versatile", temperature=0.7, max_retries=1) -> dict:
    """Call Groq LLM and parse JSON response with retry logic."""
    for attempt in range(max_retries + 1):
        t = 0.0 if attempt > 0 else temperature
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=t,
        )
        content = response.choices[0].message.content
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if attempt < max_retries:
                logger.warning("JSON parse failed on attempt %d, retrying at temperature=0.0", attempt + 1)
            else:
                raise LLMParseError(f"LLM did not return valid JSON after {max_retries + 1} attempts. Last content: {content[:200]}")
