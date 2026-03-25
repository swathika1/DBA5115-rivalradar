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

DOMAIN_TARGETS = {
    "fintech_neobanks": {
        "description": "Digital banking and cross-border payment platforms",
        "competitors": [
            {"name": "Wise", "urls": [
                {"url": "https://wise.com/gb/pricing/", "frequency": "weekly"},
                {"url": "https://wise.com/blog/", "frequency": "weekly"},
            ]},
            {"name": "Revolut", "urls": [
                {"url": "https://www.revolut.com/en-US/pricing/", "frequency": "weekly"},
                {"url": "https://blog.revolut.com/", "frequency": "weekly"},
            ]},
            {"name": "Mercury", "urls": [
                {"url": "https://mercury.com/pricing", "frequency": "monthly"},
                {"url": "https://mercury.com/blog", "frequency": "monthly"},
            ]},
        ],
    },
    "ecommerce_platforms": {
        "description": "E-commerce platform providers for merchants",
        "competitors": [
            {"name": "Shopify", "urls": [
                {"url": "https://www.shopify.com/pricing", "frequency": "weekly"},
                {"url": "https://www.shopify.com/blog", "frequency": "weekly"},
            ]},
            {"name": "BigCommerce", "urls": [
                {"url": "https://www.bigcommerce.com/essentials/pricing/", "frequency": "weekly"},
            ]},
            {"name": "WooCommerce", "urls": [
                {"url": "https://woocommerce.com/pricing/", "frequency": "monthly"},
            ]},
        ],
    },
    "edtech": {
        "description": "Online learning and professional education platforms",
        "competitors": [
            {"name": "Coursera", "urls": [
                {"url": "https://www.coursera.org/about/pricing", "frequency": "monthly"},
                {"url": "https://blog.coursera.org/", "frequency": "weekly"},
            ]},
            {"name": "Udemy", "urls": [
                {"url": "https://www.udemy.com/", "frequency": "monthly"},
            ]},
            {"name": "LinkedIn Learning", "urls": [
                {"url": "https://learning.linkedin.com/", "frequency": "monthly"},
            ]},
        ],
    },
    "pharma_biotech": {
        "description": "Pharmaceutical approvals, clinical trials, and patent filings",
        "competitors": [
            {"name": "FDA Approvals", "urls": [
                {"url": "https://www.fda.gov/drugs/new-drugs-fda-cders-new-molecular-entities-and-new-therapeutic-biological-products/novel-drug-approvals-fda", "frequency": "weekly"},
            ]},
            {"name": "ClinicalTrials", "urls": [
                {"url": "https://clinicaltrials.gov/search?aggFilters=status:rec", "frequency": "weekly"},
            ]},
            {"name": "Google Patents", "urls": [
                {"url": "https://patents.google.com/", "frequency": "monthly"},
            ]},
        ],
    },
    "saas_b2b": {
        "description": "B2B SaaS tools for CRM, productivity, and project management",
        "competitors": [
            {"name": c["name"], "urls": [
                {"url": c["pricing_url"], "frequency": "weekly"}
            ]} for c in COMPETITOR_TARGETS
        ],
    },
    "crm": {
        "description": "Customer Relationship Management (CRM) platforms",
        "competitors": [
            {"name": "Salesforce", "urls": [
                {"url": "https://www.salesforce.com/products/sales-cloud/pricing/", "frequency": "weekly"},
                {"url": "https://www.salesforce.com/blog/", "frequency": "weekly"},
                {"url": "https://developer.salesforce.com/", "frequency": "monthly"},
            ]},
            {"name": "HubSpot", "urls": [
                {"url": "https://www.hubspot.com/pricing/sales", "frequency": "weekly"},
                {"url": "https://www.hubspot.com/pricing/service", "frequency": "weekly"},
                {"url": "https://blog.hubspot.com/sales", "frequency": "weekly"},
            ]},
            {"name": "Pipedrive", "urls": [
                {"url": "https://www.pipedrive.com/en/pricing", "frequency": "weekly"},
                {"url": "https://www.pipedrive.com/en/blog", "frequency": "weekly"},
            ]},
        ],
    },
}
