import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from competitor_targets import DOMAIN_TARGETS
from db.schemas import ScrapeCache
from scrapers.web_scraper import CompetitorScraper

_FREQUENCY_HOURS = {
    "daily": 24,
    "weekly": 24 * 7,
    "monthly": 24 * 30,
}


class DomainScraper:
    """Scrapes competitor URLs based on domain and frequency."""
    
    def __init__(self, domain: str, frequency: str, db: Session, user_id: str):
        self.domain = domain
        self.frequency = frequency
        self.db = db
        self.user_id = user_id

    def get_due_urls(self) -> list[dict]:
        """Get URLs that are due for scraping based on cache and frequency."""
        domain_config = DOMAIN_TARGETS.get(self.domain, {})
        competitors = domain_config.get("competitors", [])
        hours = _FREQUENCY_HOURS.get(self.frequency, 24 * 7)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        due = []
        for comp in competitors:
            for url_entry in comp.get("urls", []):
                url = url_entry["url"]
                url_freq = url_entry.get("frequency", self.frequency)
                url_hours = _FREQUENCY_HOURS.get(url_freq, hours)
                url_cutoff = datetime.now(timezone.utc) - timedelta(hours=url_hours)
                cache = (
                    self.db.query(ScrapeCache)
                    .filter_by(url=url, user_id=self.user_id)
                    .first()
                )
                # Scrape if: no cache OR last_scraped_at is None OR past the cutoff (handle timezone-aware comparison safely)
                should_scrape = True
                if cache and cache.last_scraped_at:
                    try:
                        # Ensure both are timezone-aware for comparison
                        last_scraped = cache.last_scraped_at
                        if last_scraped.tzinfo is None:
                            last_scraped = last_scraped.replace(tzinfo=timezone.utc)
                        should_scrape = last_scraped < url_cutoff
                    except Exception:
                        should_scrape = True
                
                if should_scrape:
                    due.append({"name": comp["name"], "url": url, "page_type": "pricing"})
        return due

    async def scrape(self) -> list[dict]:
        """Scrape all due URLs asynchronously."""
        due_urls = self.get_due_urls()
        if not due_urls:
            return []
        loop = asyncio.get_event_loop()
        results = []
        scraper = CompetitorScraper(config={})
        for entry in due_urls:
            url = entry["url"]
            page_type = entry.get("page_type", "pricing")
            raw = await loop.run_in_executor(
                None, scraper.scrape_with_fallback, url, page_type
            )
            pricing = scraper.extract_pricing_data(raw.get("raw_text", ""))
            profile = {
                "name": entry["name"],
                "url": url,
                "scraped_at": raw.get("scraped_at"),
                "plans": pricing["plans"],
                "prices": pricing["prices"],
                "raw_mentions": pricing["raw_mentions"],
            }
            results.append(profile)
            self._update_cache(url, raw.get("raw_text", ""))
        return results

    def _update_cache(self, url: str, content: str):
        """Update scrape cache with new content hash and timestamp."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        cache = (
            self.db.query(ScrapeCache)
            .filter_by(url=url, user_id=self.user_id)
            .first()
        )
        if cache is None:
            cache = ScrapeCache(url=url, user_id=self.user_id)
            self.db.add(cache)
        cache.last_scraped_at = datetime.now(timezone.utc)
        cache.content_hash = content_hash
        self.db.commit()
