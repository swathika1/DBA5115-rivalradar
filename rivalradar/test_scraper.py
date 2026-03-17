"""
Standalone scraper smoke-test.
Run from the rivalradar/ directory:  python test_scraper.py
"""

import os
import sys

# Make sure local packages resolve when running as a script
sys.path.insert(0, os.path.dirname(__file__))

from competitor_targets import COMPETITOR_TARGETS
from scrapers.web_scraper import CompetitorScraper

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "scraper_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class _MinimalConfig:
    """Thin stand-in so CompetitorScraper does not need the real Config."""
    pass


def _save_raw(company_name: str, text: str):
    safe_name = company_name.lower().replace(" ", "_")
    path = os.path.join(OUTPUT_DIR, f"{safe_name}_raw.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def main():
    scraper = CompetitorScraper(_MinimalConfig())
    summary_rows: list[tuple] = []

    for target in COMPETITOR_TARGETS:
        name = target["name"]
        url = target["pricing_url"]
        print(f"\n{'=' * 60}")
        print(f"Company : {name}")
        print(f"URL     : {url}")

        result = scraper.scrape_with_fallback(url, "pricing")

        status = result.get("status_code", "ERR")
        raw_text = result.get("raw_text", "")
        fetch_method = result.get("fetch_method", "unknown")
        char_count = len(raw_text)
        error = result.get("error")

        print(f"Status  : {status}  |  Method: {fetch_method}  |  Chars: {char_count}")

        if error:
            print(f"Error   : {error}")

        print(f"\n--- First 500 chars of raw_text ---")
        print(raw_text[:500] or "(empty)")

        pricing = scraper.extract_pricing_data(raw_text)
        print(f"\n--- extract_pricing_data() ---")
        print(f"  plans        : {pricing['plans']}")
        print(f"  prices       : {pricing['prices']}")
        print(f"  raw_mentions : {pricing['raw_mentions']}")
        prices_found = len(pricing["prices"]) > 0
        print(f"  Dollar amounts found: {prices_found}")

        saved_path = _save_raw(name, raw_text)
        print(f"\nSaved  → {saved_path}")

        xpath_elements = len(raw_text.splitlines()) if raw_text else 0
        summary_rows.append((name, status, char_count, prices_found, xpath_elements, fetch_method))

    # Summary table
    print(f"\n\n{'=' * 75}")
    print(f"{'SUMMARY':^75}")
    print(f"{'=' * 75}")
    header = f"{'Company':<12} {'Status':>6}  {'Chars':>7}  {'Prices Found':>12}  {'XPath Elements':>14}  {'Method':<8}"
    print(header)
    print("-" * 75)
    for name, status, chars, prices_found, xpath_els, method in summary_rows:
        print(
            f"{name:<12} {str(status):>6}  {chars:>7}  {str(prices_found):>12}  {xpath_els:>14}  {method:<8}"
        )
    print(f"{'=' * 75}\n")


if __name__ == "__main__":
    main()
