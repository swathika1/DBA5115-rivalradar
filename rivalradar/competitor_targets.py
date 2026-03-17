"""
Known competitor targets used for scraper testing and pipeline seeding.
Each entry is a plain dict — no database dependency.
"""

COMPETITOR_TARGETS = [
    {
        "name": "HubSpot",
        "domain": "hubspot.com",
        "pricing_url": "https://www.hubspot.com/pricing/marketing",
        "page_types": ["pricing", "changelog", "blog", "integrations"],
        "market_segment": "B2B SaaS / CRM & Marketing",
    },
    {
        "name": "Notion",
        "domain": "notion.so",
        "pricing_url": "https://www.notion.so/pricing",
        "page_types": ["pricing", "blog", "integrations"],
        "market_segment": "B2B SaaS / Productivity & Docs",
    },
    {
        "name": "Linear",
        "domain": "linear.app",
        "pricing_url": "https://linear.app/pricing",
        "page_types": ["pricing", "changelog", "integrations"],
        "market_segment": "B2B SaaS / Project Management",
    },
    {
        "name": "ClickUp",
        "domain": "clickup.com",
        "pricing_url": "https://clickup.com/pricing",
        "page_types": ["pricing", "blog", "integrations", "press"],
        "market_segment": "B2B SaaS / Project Management",
    },
    {
        "name": "Stripe",
        "domain": "stripe.com",
        "pricing_url": "https://stripe.com/pricing",
        "page_types": ["pricing", "blog", "integrations", "press"],
        "market_segment": "B2B SaaS / Payments",
    },
]
