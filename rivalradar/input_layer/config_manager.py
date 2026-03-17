import json

from database.db_manager import DatabaseManager

VALID_PAGE_TYPES = {"pricing", "changelog", "blog", "integrations", "press"}


class InputConfigManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    # ------------------------------------------------------------------ #
    # Competitors                                                          #
    # ------------------------------------------------------------------ #

    def add_competitor(
        self,
        name: str,
        domain: str,
        page_types: list[str],
        market_segment: str,
    ) -> int:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError("domain must be a non-empty string")
        if not isinstance(market_segment, str) or not market_segment.strip():
            raise ValueError("market_segment must be a non-empty string")

        if not isinstance(page_types, list):
            raise TypeError(f"page_types must be a list, got {type(page_types).__name__}")
        if not page_types:
            raise ValueError("page_types must not be empty")
        invalid = [p for p in page_types if p not in VALID_PAGE_TYPES]
        if invalid:
            raise ValueError(
                f"Invalid page_types: {invalid}. Allowed values: {sorted(VALID_PAGE_TYPES)}"
            )

        return self.db.insert(
            "competitors",
            {
                "name": name.strip(),
                "domain": domain.strip(),
                "page_types": json.dumps(page_types),
                "market_segment": market_segment.strip(),
            },
        )

    # ------------------------------------------------------------------ #
    # Portfolio companies                                                  #
    # ------------------------------------------------------------------ #

    def add_portfolio_company(
        self,
        name: str,
        market_segment: str,
        product_description: str,
        features_list: list[str],
        pricing_context: str,
    ) -> int:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(market_segment, str) or not market_segment.strip():
            raise ValueError("market_segment must be a non-empty string")
        if not isinstance(product_description, str) or not product_description.strip():
            raise ValueError("product_description must be a non-empty string")
        if not isinstance(pricing_context, str) or not pricing_context.strip():
            raise ValueError("pricing_context must be a non-empty string")

        if not isinstance(features_list, list):
            raise TypeError(
                f"features_list must be a list, got {type(features_list).__name__}"
            )
        if not features_list:
            raise ValueError("features_list must not be empty")
        non_strings = [f for f in features_list if not isinstance(f, str)]
        if non_strings:
            raise TypeError(
                f"All items in features_list must be strings; found non-string values: {non_strings}"
            )
        blank = [f for f in features_list if not f.strip()]
        if blank:
            raise ValueError("features_list must not contain blank strings")

        return self.db.insert(
            "portfolio_companies",
            {
                "name": name.strip(),
                "market_segment": market_segment.strip(),
                "product_description": product_description.strip(),
                "features_json": json.dumps(features_list),
                "pricing_context": pricing_context.strip(),
            },
        )

    # ------------------------------------------------------------------ #
    # Retrieval                                                            #
    # ------------------------------------------------------------------ #

    def get_monitoring_targets(self) -> dict:
        competitors = self.db.fetch_all("competitors")
        for c in competitors:
            if c.get("page_types"):
                c["page_types"] = json.loads(c["page_types"])

        portfolio_companies = self.db.fetch_all("portfolio_companies")
        for p in portfolio_companies:
            if p.get("features_json"):
                p["features_json"] = json.loads(p["features_json"])

        return {"competitors": competitors, "portfolio_companies": portfolio_companies}

    # ------------------------------------------------------------------ #
    # Sample data                                                          #
    # ------------------------------------------------------------------ #

    def load_sample_data(self):
        """Populate the database with one portfolio company and three competitors
        so the pipeline can be tested without manual data entry."""

        # Portfolio company
        self.add_portfolio_company(
            name="Stackline",
            market_segment="B2B SaaS / Project Management",
            product_description=(
                "Stackline is a collaborative project management platform built for "
                "distributed engineering teams. It combines kanban boards, sprint planning, "
                "automated stand-ups, and engineering analytics in a single workspace."
            ),
            features_list=[
                "Kanban and Gantt views",
                "Sprint planning and velocity tracking",
                "Automated daily stand-up summaries",
                "GitHub and GitLab integration",
                "Team workload heatmaps",
                "Custom workflow automation",
                "Time tracking and reporting",
            ],
            pricing_context=(
                "Freemium model: free tier up to 5 users, $12/user/month (Pro), "
                "$28/user/month (Enterprise). Annual discount of 20%."
            ),
        )

        # Competitor 1
        self.add_competitor(
            name="Orbiflow",
            domain="orbiflow.io",
            page_types=["pricing", "changelog", "blog", "integrations"],
            market_segment="B2B SaaS / Project Management",
        )

        # Competitor 2
        self.add_competitor(
            name="Taskwell",
            domain="taskwell.com",
            page_types=["pricing", "blog", "press"],
            market_segment="B2B SaaS / Project Management",
        )

        # Competitor 3
        self.add_competitor(
            name="Sprintforge",
            domain="sprintforge.dev",
            page_types=["pricing", "changelog", "integrations", "press"],
            market_segment="B2B SaaS / Project Management",
        )
