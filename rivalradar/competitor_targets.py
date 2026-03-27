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
    {
        "name": "Slack",
        "domain": "slack.com",
        "pricing_url": "https://slack.com/pricing",
        "page_types": ["pricing", "blog", "integrations", "press"],
        "market_segment": "B2B SaaS / Communication",
    },
    {
        "name": "Asana",
        "domain": "asana.com",
        "pricing_url": "https://asana.com/pricing",
        "page_types": ["pricing", "blog", "integrations"],
        "market_segment": "B2B SaaS / Project Management",
    },
    {
        "name": "Monday.com",
        "domain": "monday.com",
        "pricing_url": "https://monday.com/pricing",
        "page_types": ["pricing", "blog", "integrations"],
        "market_segment": "B2B SaaS / Workflow Management",
    },
    {
        "name": "Jira",
        "domain": "atlassian.com",
        "pricing_url": "https://www.atlassian.com/software/jira/pricing",
        "page_types": ["pricing", "blog", "documentation"],
        "market_segment": "B2B SaaS / Project Management",
    },
    {
        "name": "Salesforce",
        "domain": "salesforce.com",
        "pricing_url": "https://www.salesforce.com/products/sales-cloud/pricing/",
        "page_types": ["pricing", "blog", "developer"],
        "market_segment": "Enterprise / CRM",
    },
    {
        "name": "Pipedrive",
        "domain": "pipedrive.com",
        "pricing_url": "https://www.pipedrive.com/en/pricing",
        "page_types": ["pricing", "blog", "integrations"],
        "market_segment": "B2B SaaS / CRM",
    },
    {
        "name": "Zendesk",
        "domain": "zendesk.com",
        "pricing_url": "https://www.zendesk.com/pricing/",
        "page_types": ["pricing", "blog", "integrations"],
        "market_segment": "B2B SaaS / Customer Support",
    },
    {
        "name": "Intercom",
        "domain": "intercom.com",
        "pricing_url": "https://www.intercom.com/pricing",
        "page_types": ["pricing", "blog", "integrations"],
        "market_segment": "B2B SaaS / Customer Communication",
    },
    {
        "name": "Shopify",
        "domain": "shopify.com",
        "pricing_url": "https://www.shopify.com/pricing",
        "page_types": ["pricing", "blog", "press"],
        "market_segment": "B2B SaaS / E-commerce",
    },
    {
        "name": "BigCommerce",
        "domain": "bigcommerce.com",
        "pricing_url": "https://www.bigcommerce.com/essentials/pricing/",
        "page_types": ["pricing", "blog"],
        "market_segment": "B2B SaaS / E-commerce",
    },
    {
        "name": "Coursera",
        "domain": "coursera.org",
        "pricing_url": "https://www.coursera.org/about/pricing",
        "page_types": ["pricing", "blog"],
        "market_segment": "B2B SaaS / EdTech",
    },
    {
        "name": "Udemy",
        "domain": "udemy.com",
        "pricing_url": "https://www.udemy.com/",
        "page_types": ["pricing", "blog"],
        "market_segment": "B2B SaaS / EdTech",
    },
    {
        "name": "Wise",
        "domain": "wise.com",
        "pricing_url": "https://wise.com/gb/pricing/",
        "page_types": ["pricing", "blog", "press"],
        "market_segment": "FinTech / Payments",
    },
    {
        "name": "Revolut",
        "domain": "revolut.com",
        "pricing_url": "https://www.revolut.com/en-US/pricing/",
        "page_types": ["pricing", "blog"],
        "market_segment": "FinTech / Banking",
    },
    {
        "name": "Mercury",
        "domain": "mercury.com",
        "pricing_url": "https://mercury.com/pricing",
        "page_types": ["pricing", "blog", "press"],
        "market_segment": "FinTech / Business Banking",
    },
    {
        "name": "Google Workspace",
        "domain": "google.com/workspace",
        "pricing_url": "https://workspace.google.com/pricing.html",
        "page_types": ["pricing", "blog"],
        "market_segment": "B2B SaaS / Productivity",
    },
    {
        "name": "Microsoft 365",
        "domain": "microsoft.com",
        "pricing_url": "https://www.microsoft.com/en-us/microsoft-365/business/microsoft-365-business-standard",
        "page_types": ["pricing", "blog"],
        "market_segment": "Enterprise / Productivity",
    },
    {
        "name": "Figma",
        "domain": "figma.com",
        "pricing_url": "https://www.figma.com/pricing/",
        "page_types": ["pricing", "blog", "community"],
        "market_segment": "B2B SaaS / Design",
    },
    {
        "name": "Miro",
        "domain": "miro.com",
        "pricing_url": "https://miro.com/pricing/",
        "page_types": ["pricing", "blog", "integrations"],
        "market_segment": "B2B SaaS / Collaboration",
    },
    {
        "name": "Loom",
        "domain": "loom.com",
        "pricing_url": "https://www.loom.com/pricing",
        "page_types": ["pricing", "blog"],
        "market_segment": "B2B SaaS / Video",
    },
    {
        "name": "GitHub",
        "domain": "github.com",
        "pricing_url": "https://github.com/pricing",
        "page_types": ["pricing", "blog", "documentation"],
        "market_segment": "Developer / Version Control",
    },
    {
        "name": "GitLab",
        "domain": "gitlab.com",
        "pricing_url": "https://about.gitlab.com/pricing/",
        "page_types": ["pricing", "blog"],
        "market_segment": "Developer / DevOps",
    },
    {
        "name": "AWS",
        "domain": "aws.amazon.com",
        "pricing_url": "https://aws.amazon.com/pricing/",
        "page_types": ["pricing", "blog", "documentation"],
        "market_segment": "Enterprise / Cloud Infrastructure",
    },
    {
        "name": "Azure",
        "domain": "azure.microsoft.com",
        "pricing_url": "https://azure.microsoft.com/en-us/pricing/",
        "page_types": ["pricing", "blog"],
        "market_segment": "Enterprise / Cloud Infrastructure",
    },
    {
        "name": "Google Cloud",
        "domain": "cloud.google.com",
        "pricing_url": "https://cloud.google.com/pricing",
        "page_types": ["pricing", "blog"],
        "market_segment": "Enterprise / Cloud Infrastructure",
    },
    {
        "name": "Datadog",
        "domain": "datadoghq.com",
        "pricing_url": "https://www.datadoghq.com/pricing/",
        "page_types": ["pricing", "blog", "documentation"],
        "market_segment": "B2B SaaS / Monitoring",
    },
    {
        "name": "New Relic",
        "domain": "newrelic.com",
        "pricing_url": "https://newrelic.com/pricing",
        "page_types": ["pricing", "blog"],
        "market_segment": "B2B SaaS / Observability",
    },
    {
        "name": "Sentry",
        "domain": "sentry.io",
        "pricing_url": "https://sentry.io/pricing/",
        "page_types": ["pricing", "blog", "documentation"],
        "market_segment": "Developer / Error Tracking",
    },
    {
        "name": "Twilio",
        "domain": "twilio.com",
        "pricing_url": "https://www.twilio.com/pricing",
        "page_types": ["pricing", "blog", "documentation"],
        "market_segment": "Developer / Communications API",
    },
    {
        "name": "SendGrid",
        "domain": "sendgrid.com",
        "pricing_url": "https://sendgrid.com/pricing/",
        "page_types": ["pricing", "blog"],
        "market_segment": "B2B SaaS / Email",
    },
    {
        "name": "Auth0",
        "domain": "auth0.com",
        "pricing_url": "https://auth0.com/pricing",
        "page_types": ["pricing", "blog", "documentation"],
        "market_segment": "Developer / Identity",
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
