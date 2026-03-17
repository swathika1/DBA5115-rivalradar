"""
Crawlee-based scraper smoke-test for RivalRadar.

Run from the rivalradar/ directory:
    python test_scraper.py

What this does:
  - Scrapes all competitor pricing pages using PlaywrightCrawler (headless Firefox)
  - Extracts plan names and price amounts from each page
  - Saves raw text to scraper_output/<company>_raw.txt
  - Prints a summary table

No API key needed for local runs.
For proxy rotation (avoids blocks in production), set APIFY_TOKEN in .env
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from competitor_targets import COMPETITOR_TARGETS
from scrapers.crawlee_scraper import CrawleeScraper
from scrapers.output_parser import parse_pricing_page, print_profile, save_structured

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "scraper_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _save_raw(company_name: str, text: str) -> str:
    safe_name = company_name.lower().replace(" ", "_")
    path = os.path.join(OUTPUT_DIR, f"{safe_name}_raw.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


async def main():
    # Build target list: one entry per competitor's pricing page
    targets = [
        {
            "url": t["pricing_url"],
            "page_type": "pricing",
            "name": t["name"],
        }
        for t in COMPETITOR_TARGETS
    ]

    print(f"Launching Crawlee PlaywrightCrawler for {len(targets)} targets...\n")
    scraper = CrawleeScraper()

    results = await scraper.scrape_pages(targets)

    summary_rows = []

    for result in results:
        name = result["name"]
        url = result["url"]
        raw_text = result["raw_text"]
        pricing = result["pricing"]
        char_count = result["char_count"]
        method = result["fetch_method"]

        print(f"\n{'=' * 62}")
        print(f"Company  : {name}")
        print(f"URL      : {url}")
        print(f"Method   : {method}  |  Chars: {char_count}")
        print(f"\n--- First 500 chars ---")
        print(raw_text[:500] or "(empty)")
        print(f"\n--- Pricing extraction ---")
        print(f"  plans        : {pricing.get('plans', [])}")
        print(f"  prices       : {pricing.get('prices', [])}")
        print(f"  raw_mentions : {pricing.get('raw_mentions', [])}")

        prices_found = len(pricing.get("prices", [])) > 0
        saved_path = _save_raw(name, raw_text)
        print(f"\nSaved raw → {saved_path}")

        # Parse into structured format and save JSON
        profile = parse_pricing_page(
            raw_text=raw_text,
            company=name,
            url=url,
            scraped_at=result["scraped_at"],
        )
        json_path = save_structured(profile, OUTPUT_DIR)
        print(f"Saved JSON → {json_path}")
        print_profile(profile)

        plan_count = len(profile.get("plans", []))
        summary_rows.append((name, char_count, prices_found, plan_count, method))

    # Summary table
    print(f"\n\n{'=' * 65}")
    print(f"{'SUMMARY':^65}")
    print(f"{'=' * 65}")
    print(f"{'Company':<12}  {'Chars':>7}  {'Prices Found':>12}  {'Plans':>5}  {'Method':<10}")
    print("-" * 70)
    for name, chars, prices_found, plan_count, method in summary_rows:
        print(f"{name:<12}  {chars:>7}  {str(prices_found):>12}  {plan_count:>5}  {method:<10}")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    asyncio.run(main())
