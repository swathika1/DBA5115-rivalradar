import logging
import random
import re
import time
from datetime import datetime, timezone

import requests
from lxml import html

logger = logging.getLogger(__name__)

# Rotate through several real Chrome UA strings so repeated requests from the
# same session don't always present an identical fingerprint.
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Realistic browser headers that accompany every request
_BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "DNT": "1",
}

# Delay range (seconds) between requests — polite crawling
_DELAY_MIN = 4.0
_DELAY_MAX = 9.0

# Playwright: selectors to wait for before grabbing HTML (page_type → CSS selector)
_PLAYWRIGHT_WAIT_SELECTORS = {
    "pricing": "[class*='price'],[class*='plan'],[class*='tier'],[class*='billing'],[class*='amount']",
    "changelog": "article,[class*='changelog'],[class*='release']",
    "blog": "article,h1",
    "integrations": "[class*='integration'],[class*='partner']",
    "press": "article,h1",
}
_PLAYWRIGHT_WAIT_TIMEOUT_MS = 15_000  # give JS up to 15 s to render target nodes
_PLAYWRIGHT_SETTLE_S = (3.0, 5.0)    # random pause after load before grabbing DOM

# XPath expressions keyed by page_type
_XPATHS: dict[str, list[str]] = {
    "pricing": [
        "//div[contains(@class,'price')]",
        "//span[contains(@class,'price')]",
        "//*[contains(@class,'plan-name')]",
        "//*[contains(@class,'amount')]",
        "//*[contains(@class,'plan')]",
        "//*[contains(@class,'tier')]",
        "//*[contains(@class,'cost')]",
        "//*[contains(@class,'billing')]",
    ],
    "changelog": [
        "//article",
        "//div[contains(@class,'changelog')]",
        "//div[contains(@class,'release')]",
        "//div[contains(@class,'version')]",
        "//div[contains(@class,'update')]",
        "//h2",
        "//h3",
    ],
    "blog": [
        "//h1",
        "//h2",
        "//article",
        "//p",
    ],
    "integrations": [
        "//*[contains(@class,'integration')]",
        "//*[contains(@class,'partner')]",
        "//*[contains(@class,'app')]",
        "//*[contains(@class,'connect')]",
        "//a[contains(@href,'integration')]",
    ],
    "press": [
        "//article",
        "//h1",
        "//h2",
        "//time",
    ],
}

# Price regex: require the numeric part to be 1–7 digits (filters out CSS counter
# animation strings like $01234567890123...).
_PRICE_AMOUNT_RE = re.compile(
    r"(?:\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?!\d)"
    r"|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?/mo\b"
    r"|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*per\s*mo(?:nth)?\b)"
)
_PRICE_CYCLE_RE = re.compile(r"[\d,]+\s*(?:per|/)\s*(?:month|year|mo|yr)", re.IGNORECASE)
_PLAN_NAME_RE = re.compile(
    r"\b(free|starter|basic|pro|professional|business|enterprise|team|growth|plus|premium)\b",
    re.IGNORECASE,
)

# Minimum raw_text length that counts as a successful static fetch
_JS_RENDER_THRESHOLD = 300


class CompetitorScraper:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(_BASE_HEADERS)
        self._last_request_time: float = 0.0

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def scrape_page(self, url: str, page_type: str) -> dict:
        self._polite_delay()

        ua = random.choice(_USER_AGENTS)
        self.session.headers["User-Agent"] = ua

        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.warning("Static fetch failed for %s: %s", url, exc)
            return {
                "url": url,
                "page_type": page_type,
                "raw_text": "",
                "status_code": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }

        raw_text = self._extract_text(response.text, page_type)
        logger.info("Static fetch OK  %s — %d chars", url, len(raw_text))

        return {
            "url": url,
            "page_type": page_type,
            "raw_text": raw_text,
            "status_code": response.status_code,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    def extract_pricing_data(self, text: str) -> dict:
        # If it looks like HTML, strip tags first
        if "<" in text and ">" in text:
            try:
                tree = html.fromstring(text)
                visible_text = " ".join(tree.text_content().split())
            except Exception:
                visible_text = text
        else:
            visible_text = text

        prices = _PRICE_AMOUNT_RE.findall(visible_text)
        cycle_mentions = _PRICE_CYCLE_RE.findall(visible_text)
        plan_matches = _PLAN_NAME_RE.findall(visible_text)

        plans = list(dict.fromkeys(p.lower() for p in plan_matches))
        unique_prices = list(dict.fromkeys(prices))
        raw_mentions = list(dict.fromkeys(prices + cycle_mentions))

        return {
            "plans": plans,
            "prices": unique_prices,
            "raw_mentions": raw_mentions,
        }

    def scrape_with_fallback(self, url: str, page_type: str) -> dict:
        """Try static scraping first; fall back to headless Playwright if the
        page appears JS-rendered.

        Fallback triggers when ANY of these are true:
          - raw_text is under _JS_RENDER_THRESHOLD characters
          - page_type is "pricing" and no dollar amounts were found in the text
        """
        result = self.scrape_page(url, page_type)

        if result.get("error"):
            result["fetch_method"] = "static"
            return result

        raw_text = result.get("raw_text", "")
        too_short = len(raw_text) < _JS_RENDER_THRESHOLD
        no_prices = page_type == "pricing" and not _PRICE_AMOUNT_RE.search(raw_text)

        if not too_short and not no_prices:
            result["fetch_method"] = "static"
            return result

        reason = "sparse text" if too_short else "no dollar amounts in pricing page"
        logger.info("Static result insufficient (%s) for %s — trying Playwright", reason, url)
        result = self._render_with_playwright(url, page_type, result)
        return result

    def check_for_changes(self, current_data: dict, previous_data: dict) -> bool:
        if current_data.get("error") or previous_data.get("error"):
            return False

        current_text = current_data.get("raw_text", "")
        previous_text = previous_data.get("raw_text", "")

        if not current_text or not previous_text:
            return False

        return " ".join(current_text.split()) != " ".join(previous_text.split())

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _polite_delay(self):
        """Sleep long enough that at least _DELAY_MIN seconds have elapsed since
        the previous request, plus a random extra buffer."""
        elapsed = time.monotonic() - self._last_request_time
        target = random.uniform(_DELAY_MIN, _DELAY_MAX)
        wait = max(0.0, target - elapsed)
        if wait > 0:
            logger.debug("Polite delay: sleeping %.1f s", wait)
            time.sleep(wait)
        self._last_request_time = time.monotonic()

    def _render_with_playwright(self, url: str, page_type: str, fallback_result: dict) -> dict:
        try:
            from playwright.sync_api import TimeoutError as PWTimeout  # noqa: PLC0415
            from playwright.sync_api import sync_playwright  # noqa: PLC0415
        except ImportError:
            logger.warning(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
            fallback_result["fetch_method"] = "static"
            fallback_result["playwright_note"] = (
                "Playwright not installed — static result returned."
            )
            return fallback_result

        ua = random.choice(_USER_AGENTS)
        wait_selector = _PLAYWRIGHT_WAIT_SELECTORS.get(page_type)

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=ua,
                    locale="en-US",
                    viewport={"width": 1280, "height": 900},
                    extra_http_headers={
                        k: v for k, v in _BASE_HEADERS.items()
                        if k not in ("Accept-Encoding",)  # Playwright handles this itself
                    },
                )
                page = context.new_page()

                # Navigate and wait for the network to settle
                page.goto(url, timeout=30_000, wait_until="domcontentloaded")

                # Then wait for the specific pricing/content selector to appear
                if wait_selector:
                    try:
                        page.wait_for_selector(
                            wait_selector, timeout=_PLAYWRIGHT_WAIT_TIMEOUT_MS
                        )
                    except PWTimeout:
                        logger.warning(
                            "Playwright selector '%s' not found within timeout for %s",
                            wait_selector, url,
                        )

                # Small human-like pause before grabbing the DOM
                time.sleep(random.uniform(*_PLAYWRIGHT_SETTLE_S))
                # inner_text("body") returns fully rendered visible text —
                # more reliable than re-running XPath over raw HTML for JS pages
                raw_text = page.inner_text("body")
                browser.close()
            raw_text = " ".join(raw_text.split())  # normalise whitespace
            logger.info("Playwright render OK  %s — %d chars", url, len(raw_text))
            fallback_result["raw_text"] = raw_text
            fallback_result["fetch_method"] = "rendered"

        except Exception as exc:
            logger.error("Playwright render failed for %s: %s", url, exc)
            fallback_result["fetch_method"] = "static"
            fallback_result["playwright_error"] = str(exc)

        return fallback_result

    def _extract_text(self, html_text: str, page_type: str) -> str:
        try:
            tree = html.fromstring(html_text)
        except Exception:
            return html_text

        xpaths = _XPATHS.get(page_type, ["//body"])
        seen: set[str] = set()
        chunks: list[str] = []

        for xpath in xpaths:
            try:
                elements = tree.xpath(xpath)
            except Exception:
                continue
            for el in elements:
                text = " ".join(el.text_content().split())
                if text and text not in seen:
                    seen.add(text)
                    chunks.append(text)

        return "\n".join(chunks)
