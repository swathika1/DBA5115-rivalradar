"""
Single-run pipeline: scrape competitor pricing pages and analyze vulnerability.

Run from the rivalradar/ directory:
    python run_scrape_and_analyze.py
"""

import asyncio
import os

from agents.agent2_analyzer import (
    analyze_profiles,
    print_vulnerability_report,
    save_vulnerability_report,
)
from agents.agent3_pricing import (
    predict_pricing_changes,
    print_pricing_predictions,
    save_pricing_predictions,
)
from agents.agent4_actions import (
    generate_action_recommendations,
    print_action_recommendations,
    save_action_recommendations,
)
from competitor_targets import COMPETITOR_TARGETS
from scrapers.crawlee_scraper import CrawleeScraper
from scrapers.output_parser import parse_pricing_page, save_structured

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "scraper_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def run_pipeline() -> None:
    targets = [
        {
            "url": target["pricing_url"],
            "page_type": "pricing",
            "name": target["name"],
        }
        for target in COMPETITOR_TARGETS
    ]

    print(f"Running scraper for {len(targets)} competitor pricing pages...")
    scraper = CrawleeScraper()
    scrape_results = await scraper.scrape_pages(targets)

    structured_profiles: list[dict] = []
    for row in scrape_results:
        profile = parse_pricing_page(
            raw_text=row.get("raw_text", ""),
            company=row.get("name", "Unknown"),
            url=row.get("url", ""),
            scraped_at=row.get("scraped_at", ""),
        )
        save_structured(profile, OUTPUT_DIR)
        structured_profiles.append(profile)

    print("Running Agent 2 (competitive positioning analyzer)...")
    vulnerability_results = analyze_profiles(structured_profiles)
    report_path = save_vulnerability_report(vulnerability_results, OUTPUT_DIR)
    print_vulnerability_report(vulnerability_results)

    print("Running Agent 3 (pricing change prediction)...")
    pricing_predictions = predict_pricing_changes(vulnerability_results, structured_profiles)
    pricing_report_path = save_pricing_predictions(pricing_predictions, OUTPUT_DIR)
    print_pricing_predictions(pricing_predictions)

    print("Running Agent 4 (portfolio action recommendations)...")
    action_recommendations = generate_action_recommendations(
        vulnerability_results,
        pricing_predictions,
    )
    action_report_path = save_action_recommendations(action_recommendations, OUTPUT_DIR)
    print_action_recommendations(action_recommendations)

    print(f"Saved all reports to: {OUTPUT_DIR}")
    print(f"Agent 2 report: {report_path}")
    print(f"Agent 3 report: {pricing_report_path}")
    print(f"Agent 4 report: {action_report_path}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
