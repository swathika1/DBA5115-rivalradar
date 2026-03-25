import asyncio
import logging
from sqlalchemy.orm import Session
from scrapers.domain_scrapers import DomainScraper
from db.schemas import PipelineRun

logger = logging.getLogger(__name__)


class Agent1:
    """Collector Agent - Scrapes competitor data and returns structured profiles."""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    async def collect(self, domain: str, frequency: str, competitors: list[str] | None = None) -> dict:
        """
        Collect competitor profiles from DOMAIN_TARGETS.
        Falls back to cached pipeline_run if scraping fails.
        """
        # Normalize domain name (convert to lowercase)
        normalized_domain = domain.lower() if domain else "saas_b2b"
        
        scraper = DomainScraper(normalized_domain, frequency, self.db, self.user_id)
        try:
            profiles = await scraper.scrape()
        except Exception as exc:
            logger.warning("DomainScraper failed: %s — falling back to DB cache", exc)
            profiles = []

        if not profiles:
            logger.info("No profiles scraped — loading from DB cache for user %s", self.user_id)
            last_run = (
                self.db.query(PipelineRun)
                .filter_by(user_id=self.user_id)
                .order_by(PipelineRun.created_at.desc())
                .first()
            )
            if last_run and last_run.agent1_output:
                return last_run.agent1_output
            return {"structured_profiles": []}

        return {"structured_profiles": profiles}
