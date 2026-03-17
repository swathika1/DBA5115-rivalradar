"""
Structured parser for raw SaaS pricing page text.

Takes the flat single-line text produced by CrawleeScraper and extracts:
  - Individual pricing plans (name, price, billing period, key features)
  - A pricing summary (free tier, enterprise tier, price range)
  - Cleaned text with nav/footer noise removed

Output schema (saved as <company>_structured.json):
{
    "company":  str,
    "url":      str,
    "scraped_at": str,
    "plans": [
        {
            "name":     str,          # "Free", "Pro", "Business", etc.
            "price":    str,          # "$0", "$10", "Contact sales"
            "billing":  str,          # "per user/month" | "per month" | "free" | "custom"
            "features": [str, ...]    # key feature bullets for this plan
        },
        ...
    ],
    "pricing_summary": {
        "free_tier":       bool,
        "enterprise_tier": bool,
        "plan_names":      [str],
        "price_range":     str        # "$0 – $20"
    },
    "raw_char_count": int
}
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical plan names in rough tier order (also used for detection)
_PLAN_NAMES = [
    "free forever", "free", "starter", "basic", "unlimited", "essential",
    "essentials", "plus", "standard", "professional", "pro", "team",
    "growth", "premium", "business", "scale", "enterprise",
    "brain ai", "everything ai",        # ClickUp AI tiers
]

# Words/phrases that indicate a new plan section is starting.
# Pattern: plan-name token(s) immediately before or after a price token.
_PLAN_NAME_RE = re.compile(
    r"\b(Free(?:\s+Forever)?|Starter|Basic|Unlimited|Essential(?:s)?|Plus|"
    r"Standard|Pro(?:fessional)?|Team|Growth|Premium|Business|Scale|Enterprise|"
    r"Brain\s+AI|Everything\s+AI)\b",
    re.IGNORECASE,
)

# Price patterns: "$9", "$9.99", "$1,200", "9/mo", "Contact sales/us"
_PRICE_RE = re.compile(
    r"(\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?/mo"
    r"|Contact\s+(?:sales|us))",
    re.IGNORECASE,
)

# Billing period patterns
_BILLING_RE = re.compile(
    r"(per\s+(?:user[\s/]*)?(?:month|year)|/\s*(?:month|year|mo|yr)"
    r"|billed\s+(?:yearly|monthly|annually)|per\s+seat/month"
    r"|per\s+member\s*/\s*month|free\s+(?:forever|for\s+everyone))",
    re.IGNORECASE,
)

# Noise: nav links, footer items, CTAs, cookie banners, FAQ boilerplate
_NOISE_TOKENS = {
    "get started", "contact us", "contact sales", "log in", "login",
    "sign up", "sign in", "get notion free", "get a demo", "request a demo",
    "learn more", "skip to content", "load more", "watch video",
    "privacy", "terms", "cookie", "status", "careers", "about us",
    "about", "customers", "partners", "affiliates", "press", "blog",
    "security", "changelog", "integrations", "download", "ios", "android",
    "windows", "mac", "frequently asked questions", "find answers",
    "© 2025", "© 2026", "soc 2", "iso 27001", "gdpr", "hipaa",
    "trusted by", "powering the world", "meet our customers",
}

# Feature lines that are generic noise (comparison table repetition)
_FEATURE_NOISE_RE = re.compile(
    r"^(all \w+ features?\s*\+?|everything in \w+.*?\+?|includes?:?)$",
    re.IGNORECASE,
)

# Minimum word count for a token to be considered a feature bullet
_MIN_FEATURE_WORDS = 2
# Maximum feature bullets to keep per plan (avoids dumping the comparison table)
_MAX_FEATURES = 12


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pricing_page(
    raw_text: str,
    company: str,
    url: str = "",
    scraped_at: str = "",
) -> dict:
    """
    Parse a flat raw-text pricing page into a structured dict.

    Parameters
    ----------
    raw_text : str
        Single-line whitespace-normalised text from the scraper.
    company  : str   e.g. "Linear"
    url      : str   original URL
    scraped_at: str  ISO timestamp

    Returns
    -------
    Structured dict matching the schema at the top of this file.
    """
    cleaned = _strip_noise(raw_text)

    # Stripe (and similar payment processors) use per-transaction pricing,
    # not a plan-tier structure.  Detect this and return a simplified profile.
    if _is_transactional_pricing(cleaned):
        prices = sorted(
            set(_PRICE_RE.findall(cleaned)),
            key=lambda s: float(re.sub(r"[^\d.]", "", s) or "0"),
        )
        return {
            "company":   company,
            "url":       url,
            "scraped_at": scraped_at or datetime.now(timezone.utc).isoformat(),
            "pricing_model": "transaction_based",
            "note": (
                "This provider uses per-transaction / usage-based pricing "
                "rather than fixed plan tiers."
            ),
            "sample_rates": prices[:15],
            "pricing_summary": {
                "free_tier": False,
                "enterprise_tier": bool(re.search(r"\benterprise\b", cleaned, re.I)),
                "plan_names": [],
                "price_range": f"{prices[0]} – {prices[-1]}" if len(prices) >= 2 else "N/A",
            },
            "raw_char_count": len(raw_text),
        }

    plans   = _extract_plans(cleaned)
    summary = _build_summary(plans)

    return {
        "company":         company,
        "url":             url,
        "scraped_at":      scraped_at or datetime.now(timezone.utc).isoformat(),
        "plans":           plans,
        "pricing_summary": summary,
        "raw_char_count":  len(raw_text),
    }


def save_structured(profile: dict, output_dir: str | Path) -> Path:
    """Save a structured profile to <output_dir>/<company>_structured.json."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = profile["company"].lower().replace(" ", "_")
    out_path   = output_dir / f"{safe_name}_structured.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2, ensure_ascii=False)
    return out_path


def print_profile(profile: dict) -> None:
    """Pretty-print a structured profile to stdout."""
    c   = profile["company"]
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {c.upper()} — Pricing Structure")
    print(sep)

    # Transaction-based (e.g. Stripe)
    if profile.get("pricing_model") == "transaction_based":
        print(f"\n  Model  : Transaction / usage-based pricing")
        print(f"  Note   : {profile['note']}")
        print(f"  Rates  : {', '.join(profile.get('sample_rates', []))}")
    else:
        for plan in profile.get("plans", []):
            price   = plan["price"]
            billing = plan["billing"]
            badge   = f"{price}  ({billing})" if billing else price
            print(f"\n  [{plan['name']}]  {badge}")
            for feat in plan["features"]:
                print(f"    • {feat}")

    s = profile["pricing_summary"]
    print(f"\n  Summary:")
    if s.get("plan_names"):
        print(f"    Plans        : {', '.join(s['plan_names'])}")
    print(f"    Price range  : {s['price_range']}")
    print(f"    Free tier    : {'Yes' if s['free_tier'] else 'No'}")
    print(f"    Enterprise   : {'Yes' if s['enterprise_tier'] else 'No'}")
    print(sep)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_transactional_pricing(text: str) -> bool:
    """Return True if the page uses per-transaction / usage-based pricing."""
    signals = [
        r"\bper\s+transaction\b",
        r"\bper\s+successful\s+charge\b",
        r"\b\d+\.\d+%\s*\+\s*\$",   # "2.9% + $0.30" style
        r"\bprocessing\s+fee\b",
        r"\bbilling\s+meter\b",
        r"\busage.based\s+billing\b",
    ]
    return sum(1 for s in signals if re.search(s, text, re.I)) >= 2


def _strip_noise(text: str) -> str:
    """
    Remove navigation, footer, cookie banners, and other non-pricing text.
    Works on normalised single-line text.
    """
    # Split into sentence-like chunks on "." or known CTA/nav boundaries
    tokens = text.split()
    cleaned: list[str] = []
    skip_next = 0

    for i, tok in enumerate(tokens):
        if skip_next > 0:
            skip_next -= 1
            continue

        # Build a 3-gram for phrase matching
        phrase2 = " ".join(tokens[i:i+2]).lower().rstrip(".,")
        phrase3 = " ".join(tokens[i:i+3]).lower().rstrip(".,")

        if phrase3 in _NOISE_TOKENS or phrase2 in _NOISE_TOKENS:
            words = len(phrase3.split()) if phrase3 in _NOISE_TOKENS else len(phrase2.split())
            skip_next = words - 1
            continue

        # Drop bare copyright / year tokens
        if re.match(r"^[©®]$|^\d{4}$", tok):
            continue

        cleaned.append(tok)

    return " ".join(cleaned)


def _extract_plans(text: str) -> list[dict]:
    """
    Split cleaned text into per-plan sections and extract structured data.

    Strategy (backward-scan — more robust than forward-scan):
      1. Find every price token position in the token stream.
      2. For each price, look BACK up to 8 tokens for the nearest plan name.
         Skip if the plan name candidate is preceded by "all", "in", "and",
         "the", "every", "from" — those indicate a descriptor, not a heading.
      3. Deduplicate by plan name (keep first occurrence in text).
      4. Also sweep for plan names with no numeric price ("Enterprise",
         "Free Forever") and insert them with a synthetic price.
      5. Sort anchors by text position, then slice feature tokens between them.
    """
    tokens = text.split()

    # ── Step 1: locate every price token ──────────────────────────────────
    raw_anchors: list[dict] = []

    for i, tok in enumerate(tokens):
        price_tok: Optional[str] = None

        m = _PRICE_RE.fullmatch(tok.rstrip(".,"))
        if m:
            price_tok = m.group(0)
        elif tok.lower() == "contact" and i + 1 < len(tokens):
            if tokens[i + 1].lower().rstrip(".,") in ("sales", "us"):
                price_tok = "Contact sales"

        if price_tok is None:
            continue

        # Skip prices that are immediately qualified as non-plan (e.g. "$200 value")
        next_tok = tokens[i + 1].lower().rstrip(".,") if i + 1 < len(tokens) else ""
        if next_tok in ("value", "worth", "off", "credit", "credits", "savings"):
            continue

        # ── Step 2: look back for plan name ───────────────────────────────
        lookback = tokens[max(0, i - 8): i]
        plan_name: Optional[str] = None
        name_pos:  int = i

        for j in range(len(lookback) - 1, -1, -1):
            prev_tok = lookback[j - 1].lower().rstrip(".,") if j > 0 else ""
            # Skip descriptors: "all free features", "everything in business"
            if prev_tok in ("all", "in", "and", "the", "every", "from",
                            "vs", "compared", "save"):
                continue

            # Try 2-token then 1-token candidate
            cand2 = " ".join(lookback[j: j + 2]) if j + 1 < len(lookback) else ""
            cand1 = lookback[j]
            for cand in (cand2, cand1):
                if cand and _PLAN_NAME_RE.fullmatch(cand.strip()):
                    plan_name = cand.strip()
                    name_pos  = max(0, i - 8) + j
                    break
            if plan_name:
                break

        if plan_name is None:
            continue

        # Billing: scan forward up to 12 tokens after the price
        fwd = " ".join(tokens[i: i + 12])
        mb  = _BILLING_RE.search(fwd)
        billing = _normalise_billing(mb.group(0)) if mb else ""

        raw_anchors.append({
            "name":      _canonical_name(plan_name),
            "name_pos":  name_pos,
            "price":     price_tok,
            "price_pos": i,
            "billing":   billing,
        })

    # ── Step 3: add priceless plans (Free Forever, Enterprise w/ Contact) ─
    # Sweep for "Free Forever" not yet in anchors
    free_names = {a["name"] for a in raw_anchors}
    for i, tok in enumerate(tokens):
        two = " ".join(tokens[i: i + 2])
        if two.lower() == "free forever" and "Free" not in free_names:
            raw_anchors.append({
                "name": "Free",  "name_pos": i,
                "price": "$0",   "price_pos": i + 1,
                "billing": "free",
            })
            free_names.add("Free")

    # Sweep for "Enterprise" with no price (Contact sales tier).
    # Skip occurrences in the nav bar (first 60 tokens) or followed by
    # a CTA like "Get a Demo" / "Log in".
    if "Enterprise" not in free_names:
        for i, tok in enumerate(tokens):
            if i < 60:
                continue  # skip nav/header area
            if _PLAN_NAME_RE.fullmatch(tok) and tok.lower() == "enterprise":
                # Confirm it's a pricing section anchor, not a navigation link.
                # If immediately followed by "Get", "Log", "Sign" → skip.
                nxt = tokens[i + 1].lower() if i + 1 < len(tokens) else ""
                if nxt in ("get", "log", "sign", "learn"):
                    continue
                raw_anchors.append({
                    "name": "Enterprise", "name_pos": i,
                    "price": "Contact sales", "price_pos": i,
                    "billing": "custom",
                })
                break

    # ── Step 4: sort, deduplicate, build plan list ─────────────────────────
    raw_anchors.sort(key=lambda a: a["price_pos"])

    seen:   set[str]    = set()
    anchors: list[dict] = []
    for a in raw_anchors:
        if a["name"] not in seen:
            seen.add(a["name"])
            anchors.append(a)

    if not anchors:
        return []

    plans: list[dict] = []
    for idx, anchor in enumerate(anchors):
        feat_start = anchor["price_pos"] + 1
        feat_end   = (anchors[idx + 1]["name_pos"]
                      if idx + 1 < len(anchors) else len(tokens))
        features   = _extract_features(tokens[feat_start:feat_end])
        plans.append({
            "name":     anchor["name"],
            "price":    anchor["price"],
            "billing":  anchor["billing"],
            "features": features,
        })

    return plans


def _extract_features(tokens: list[str]) -> list[str]:
    """
    Reconstruct feature bullets from a flat token stream.

    Heuristic: capitalised words after a lowercase run tend to start a new
    feature.  We also drop noise phrases and CTA tokens.
    """
    text = " ".join(tokens)

    # Drop well-known noise phrases inline
    for phrase in sorted(_NOISE_TOKENS, key=len, reverse=True):
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)

    # Split on capital-letter boundaries (new feature bullets tend to start
    # with a capital after a non-capital, or after "Get started" etc.)
    # Also split on common separators like " + "
    chunks = re.split(
        r"(?<=[a-z\d])\s+(?=[A-Z])|"      # lower → UPPER boundary
        r"\s+\+\s+|"                        # " + "
        r"\b(?:Get started|Sign up)\b",     # CTA markers
        text,
        flags=re.IGNORECASE,
    )

    features: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip(" .,+*")
        if not chunk:
            continue
        words = chunk.split()
        if len(words) < _MIN_FEATURE_WORDS:
            continue
        if _FEATURE_NOISE_RE.match(chunk):
            continue
        # Drop very long chunks (>12 words) — likely paragraph noise
        if len(words) > 12:
            # Keep only first sentence
            chunk = " ".join(words[:12]) + "…"
        features.append(chunk)
        if len(features) >= _MAX_FEATURES:
            break

    return features


def _normalise_billing(raw: str) -> str:
    raw = raw.strip().lower()
    if re.search(r"free|forever|everyone", raw):
        return "free"
    if re.search(r"year|annual", raw):
        return "per user/month, billed yearly"
    if re.search(r"month", raw):
        return "per user/month"
    if re.search(r"seat", raw):
        return "per seat/month"
    if re.search(r"member", raw):
        return "per member/month"
    return raw


def _canonical_name(raw: str) -> str:
    """Title-case and normalise plan names, preserving known acronyms."""
    mapping = {
        "free forever":  "Free",
        "essentials":    "Essentials",
        "brain ai":      "Brain AI",
        "everything ai": "Everything AI",
    }
    low = raw.lower()
    return mapping.get(low, raw.title())


def _build_summary(plans: list[dict]) -> dict:
    prices: list[str] = []
    for p in plans:
        tok = p["price"]
        if tok and tok.lower().startswith("contact"):
            continue
        if tok and tok.startswith("$"):
            prices.append(tok)

    # Sort numerically
    def _num(s: str) -> float:
        try:
            return float(re.sub(r"[^\d.]", "", s))
        except ValueError:
            return float("inf")

    prices.sort(key=_num)
    price_range = f"{prices[0]} – {prices[-1]}" if len(prices) >= 2 else (prices[0] if prices else "N/A")

    return {
        "free_tier":       any(p["name"].lower() == "free" for p in plans),
        "enterprise_tier": any("enterprise" in p["name"].lower() for p in plans),
        "plan_names":      [p["name"] for p in plans],
        "price_range":     price_range,
    }
