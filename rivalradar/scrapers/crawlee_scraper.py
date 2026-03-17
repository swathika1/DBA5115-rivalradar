"""
Crawlee-based competitor scraper for RivalRadar.

Uses PlaywrightCrawler (headless Firefox) as the primary engine because every
major SaaS pricing page (HubSpot, Notion, Linear, ClickUp, Stripe) is
JavaScript-rendered — static HTTP requests return skeleton HTML with no prices.

Key Crawlee APIs used:
  - PlaywrightCrawler      : headless browser crawler (Playwright under the hood)
  - Request.from_url()     : attach per-URL metadata (page_type, competitor name)
  - context.page           : full Playwright Page API
  - context.push_data()    : stream results to Crawlee's in-memory dataset
  - crawler.get_data()     : retrieve all results after the run

Apify proxy (optional, recommended for production):
  Set APIFY_TOKEN in your .env file to enable residential proxy rotation.
  Without it the crawler runs locally with no proxy — fine for dev/testing,
  but large-scale runs may hit rate limits on sites like HubSpot or ClickUp.
  Get a free token at: console.apify.com → Settings → Integrations
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from crawlee import ConcurrencySettings, Request
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns (kept identical to web_scraper.py for output compatibility)
# ---------------------------------------------------------------------------
_PRICE_AMOUNT_RE = re.compile(
    r"(?:\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?!\d)"   # $29 / $1,200 / $9.99
    r"|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?/mo\b"       # 29/mo  (HubSpot style)
    r"|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*per\s*mo(?:nth)?\b)"  # 29 per month
)
_PRICE_CYCLE_RE = re.compile(
    r"[\d,]+\s*(?:per|/)\s*(?:month|year|mo|yr)", re.IGNORECASE
)
_PLAN_NAME_RE = re.compile(
    r"\b(free|starter|basic|pro|professional|business|enterprise|team|growth|plus|premium)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Per-page-type CSS selectors Playwright waits for before reading the DOM.
# These target the actual content containers, not nav/footer chrome, so the
# crawler waits for the *relevant* section rather than just domcontentloaded.
# ---------------------------------------------------------------------------
_WAIT_SELECTORS: dict[str, str] = {
    "pricing": (
        "[class*='price'],[class*='plan'],[class*='tier'],"
        "[class*='billing'],[class*='amount'],[class*='card']"
    ),
    "changelog": "article,[class*='changelog'],[class*='release'],[class*='version']",
    "blog": "article,main h1,[class*='post']",
    "integrations": (
        "[class*='integration'],[class*='partner'],[class*='app-card'],"
        "[class*='connect'],[class*='marketplace']"
    ),
    "press": "article,[class*='press'],[class*='news'],main h1",
}

_WAIT_TIMEOUT_MS = 15_000   # give JS up to 15 s to render content selectors
_SETTLE_MS = 3_000          # extra pause after selector found (lazy-load images, etc.)


# ---------------------------------------------------------------------------
# Public scraper class
# ---------------------------------------------------------------------------

class CrawleeScraper:
    """
    Async-first Crawlee scraper.  Call scrape_pages() from an async context,
    or scrape_sync() for a blocking call (e.g. from a script or CrewAI tool).

    Usage example
    -------------
    targets = [
        {"url": "https://linear.app/pricing",  "page_type": "pricing",  "name": "Linear"},
        {"url": "https://linear.app/changelog", "page_type": "changelog","name": "Linear"},
    ]
    scraper = CrawleeScraper()
    results = scraper.scrape_sync(targets)
    """

    def __init__(self, apify_token: Optional[str] = None):
        """
        Parameters
        ----------
        apify_token:
            Apify API token for residential proxy rotation.  If None the
            scraper reads APIFY_TOKEN from the environment (set in .env).
            Leave blank for local development — no proxy is used.
        """
        self._apify_token = apify_token or os.getenv("APIFY_TOKEN")
        self._results: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Primary async API
    # ------------------------------------------------------------------

    async def scrape_pages(self, targets: list[dict]) -> list[dict]:
        """
        Scrape a list of competitor pages concurrently.

        Parameters
        ----------
        targets:
            List of dicts, each with keys:
              - url        (str)  target URL
              - page_type  (str)  one of: pricing | changelog | blog | integrations | press
              - name       (str)  human-readable competitor name (e.g. "HubSpot")

        Returns
        -------
        List of result dicts (one per URL), each containing:
          url, name, page_type, raw_text, pricing, status_code,
          scraped_at, fetch_method, char_count
        """
        self._results = {}

        proxy_config = self._build_proxy_config()

        crawler = PlaywrightCrawler(
            max_requests_per_crawl=len(targets),
            concurrency_settings=ConcurrencySettings(desired_concurrency=3, max_concurrency=3),
            headless=True,
            browser_type="firefox",     # Firefox has a lower bot-detection profile than Chromium
            proxy_configuration=proxy_config,
        )

        @crawler.router.default_handler
        async def _handler(context: PlaywrightCrawlingContext) -> None:
            url = context.request.url
            user_data = context.request.user_data or {}
            page_type = user_data.get("page_type", "pricing")
            name = user_data.get("name", url)

            context.log.info("Scraping %-12s %-14s %s", name, f"({page_type})", url)

            # ---- wait for relevant content -----------------------------------
            wait_sel = _WAIT_SELECTORS.get(page_type)
            if wait_sel:
                try:
                    await context.page.wait_for_selector(
                        wait_sel, timeout=_WAIT_TIMEOUT_MS
                    )
                    # Let lazy-loaded elements finish rendering
                    await context.page.wait_for_timeout(_SETTLE_MS)
                except Exception:
                    context.log.warning(
                        "Content selector not found within timeout for %s — "
                        "reading page as-is.", url
                    )

            # ---- extract all visible text ------------------------------------
            # inner_text("body") returns rendered text exactly as the user sees
            # it — better than innerHTML for extracting prices and plan names.
            try:
                raw_text = await context.page.inner_text("body")
            except Exception as exc:
                context.log.error("inner_text() failed for %s: %s", url, exc)
                raw_text = ""

            raw_text = " ".join(raw_text.split())   # collapse whitespace

            result = {
                "name": name,
                "url": url,
                "page_type": page_type,
                "raw_text": raw_text,
                "pricing": _extract_pricing(raw_text) if page_type == "pricing" else {},
                "status_code": context.request.loaded_url and 200,  # Playwright doesn't expose status; 200 means page loaded
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "fetch_method": "rendered",
                "char_count": len(raw_text),
            }

            self._results[url] = result
            await context.push_data(result)

        # ---- build Request objects with per-URL metadata --------------------
        requests = [
            Request.from_url(
                t["url"],
                user_data={"page_type": t["page_type"], "name": t["name"]},
            )
            for t in targets
        ]

        await crawler.run(requests)
        return list(self._results.values())

    # ------------------------------------------------------------------
    # Sync convenience wrapper (useful for scripts and CrewAI tools)
    # ------------------------------------------------------------------

    def scrape_sync(self, targets: list[dict]) -> list[dict]:
        """Blocking wrapper around scrape_pages()."""
        return asyncio.run(self.scrape_pages(targets))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_proxy_config(self):
        """
        Return an Apify ProxyConfiguration if APIFY_TOKEN is available,
        otherwise return None (direct connection, no proxy).

        Apify proxy is strongly recommended for production runs against
        sites like HubSpot or ClickUp that actively block scrapers.
        Residential proxies rotate your exit IP on every request so you
        appear as thousands of different users.
        """
        if not self._apify_token:
            logger.info(
                "No APIFY_TOKEN found — running without proxy.  "
                "Set APIFY_TOKEN in .env for residential proxy rotation."
            )
            return None

        try:
            # apify-client is installed as a dependency of the apify SDK.
            # Only import here so the class still works without it.
            from apify import ProxyConfiguration  # type: ignore
            logger.info("Apify proxy configuration enabled.")
            return ProxyConfiguration(password=self._apify_token)
        except ImportError:
            logger.warning(
                "apify package not installed — proxy disabled.  "
                "Run: pip install apify"
            )
            return None


# ---------------------------------------------------------------------------
# Standalone pricing extractor (reusable by agents)
# ---------------------------------------------------------------------------

def extract_pricing(text: str) -> dict:
    """
    Extract structured pricing data from raw page text.

    Returns a dict with:
      - plans         : list of plan name strings (deduplicated, lowercase)
      - prices        : list of dollar-amount strings e.g. ['$29', '$99']
      - raw_mentions  : all price/cycle strings found
    """
    return _extract_pricing(text)


def _extract_pricing(text: str) -> dict:
    prices = list(dict.fromkeys(_PRICE_AMOUNT_RE.findall(text)))
    cycle_mentions = list(dict.fromkeys(_PRICE_CYCLE_RE.findall(text)))
    plan_matches = list(dict.fromkeys(p.lower() for p in _PLAN_NAME_RE.findall(text)))
    return {
        "plans": plan_matches,
        "prices": prices,
        "raw_mentions": prices + cycle_mentions,
    }
