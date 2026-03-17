"""
Data quality checker for files produced by test_scraper.py.
Run from the rivalradar/ directory:  python check_data_quality.py
"""

import os
import re

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "scraper_output")

_DOLLAR_RE = re.compile(r"\$[\d,]+(?:\.\d{2})?")
_KEYWORD_RE = re.compile(
    r"\b(plan|month|year|per user|seat|free|enterprise)\b", re.IGNORECASE
)

# Score buckets
_GOOD = "GOOD"
_PARTIAL = "PARTIAL"
_POOR = "POOR"

_SCORE_ORDER = {_GOOD: 0, _PARTIAL: 1, _POOR: 2}


def _score(dollar_count: int, keyword_count: int) -> str:
    if dollar_count >= 3 and keyword_count >= 3:
        return _GOOD
    if dollar_count >= 1 or keyword_count >= 1:
        return _PARTIAL
    return _POOR


def main():
    if not os.path.isdir(OUTPUT_DIR):
        print(f"Directory not found: {OUTPUT_DIR}")
        print("Run test_scraper.py first to generate output files.")
        return

    txt_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_raw.txt")]
    if not txt_files:
        print(f"No *_raw.txt files found in {OUTPUT_DIR}")
        return

    rows: list[dict] = []

    for filename in txt_files:
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()

        dollar_matches = _DOLLAR_RE.findall(content)
        keyword_matches = _KEYWORD_RE.findall(content)
        dollar_count = len(dollar_matches)
        keyword_count = len(keyword_matches)
        grade = _score(dollar_count, keyword_count)

        company = filename.replace("_raw.txt", "").replace("_", " ").title()
        rows.append(
            {
                "company": company,
                "filename": filename,
                "dollars": dollar_count,
                "keywords": keyword_count,
                "score": grade,
                "preview": content[:300],
            }
        )

    rows.sort(key=lambda r: (_SCORE_ORDER[r["score"]], -r["dollars"], -r["keywords"]))

    # Ranked table
    print(f"\n{'=' * 65}")
    print(f"{'DATA QUALITY REPORT':^65}")
    print(f"{'=' * 65}")
    header = f"{'Company':<20}  {'$':>4}  {'KW':>4}  {'Score':<8}"
    print(header)
    print("-" * 65)
    for r in rows:
        marker = "  <-- review" if r["score"] == _POOR else ""
        print(f"{r['company']:<20}  {r['dollars']:>4}  {r['keywords']:>4}  {r['score']:<8}{marker}")

    # Detail for POOR files
    poor = [r for r in rows if r["score"] == _POOR]
    if poor:
        print(f"\n{'=' * 65}")
        print(f"POOR FILES — first 300 chars")
        print(f"{'=' * 65}")
        for r in poor:
            print(f"\n[{r['filename']}]")
            preview = r["preview"].strip()
            print(preview if preview else "(empty file)")

    print(f"\n{'=' * 65}")
    good = sum(1 for r in rows if r["score"] == _GOOD)
    partial = sum(1 for r in rows if r["score"] == _PARTIAL)
    poor_count = len(poor)
    print(f"Total: {len(rows)}  |  GOOD: {good}  PARTIAL: {partial}  POOR: {poor_count}")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    main()
