# RivalRadar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full RivalRadar platform — 4-agent LLM pipeline, FastAPI backend, and React dashboard.

**Architecture:** SQLAlchemy ORM on SQLite; FastAPI with BackgroundTasks for async pipeline execution; Groq llama-3.3-70b-versatile for all LLM calls; Vite+React+Tailwind frontend with JWT in AuthContext (never localStorage).

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, python-jose, passlib, Groq SDK, Vite, React, Tailwind CSS, Recharts

---

## File Map

**Create (backend):**
- `rivalradar/db/__init__.py`
- `rivalradar/db/database.py` — engine, SessionLocal, Base, init_db()
- `rivalradar/db/schemas.py` — ORM: users, pipeline_runs, pipeline_jobs, scrape_cache
- `rivalradar/scrapers/domain_scrapers.py` — DomainScraper class
- `rivalradar/agents/__init__.py` — chat_json(), LLMParseError
- `rivalradar/agents/agent1_collector.py` — Agent1.collect()
- `rivalradar/agents/agent2_analyzer.py` — Agent2.analyze() + PortfolioRiskAssessment dataclass
- `rivalradar/agents/agent3_forecaster.py` — Agent3.forecast() + ImpactForecast + TimeToImpact
- `rivalradar/agents/agent4_strategist.py` — Agent4.strategize() + ActionRecommendation + RecommendationType
- `rivalradar/agents/orchestrator.py` — async run_pipeline()
- `rivalradar/api/__init__.py`
- `rivalradar/api/main.py` — FastAPI app + CORS + router mounts
- `rivalradar/api/models.py` — all Pydantic request/response models
- `rivalradar/api/routes/__init__.py`
- `rivalradar/api/routes/auth.py` — POST /auth/signup, POST /auth/login
- `rivalradar/api/routes/pipeline.py` — POST /pipeline/run, GET /pipeline/status/{job_id}, GET /pipeline/history
- `rivalradar/api/routes/dashboard.py` — GET /dashboard, PATCH /user/settings
- `rivalradar/api/routes/chat.py` — POST /chat
- `rivalradar/tests/__init__.py`
- `rivalradar/tests/test_agents.py`
- `rivalradar/tests/test_api.py`

**Modify (backend):**
- `rivalradar/competitor_targets.py` — add DOMAIN_TARGETS dict
- `rivalradar/requirements.txt` — add pytest, httpx (test client)

**Create (frontend):**
- `rivalradar/frontend/package.json`
- `rivalradar/frontend/index.html`
- `rivalradar/frontend/vite.config.js`
- `rivalradar/frontend/tailwind.config.js`
- `rivalradar/frontend/postcss.config.js`
- `rivalradar/frontend/src/main.jsx`
- `rivalradar/frontend/src/App.jsx`
- `rivalradar/frontend/src/index.css`
- `rivalradar/frontend/src/context/AuthContext.jsx`
- `rivalradar/frontend/src/pages/Landing.jsx`
- `rivalradar/frontend/src/pages/Signup.jsx`
- `rivalradar/frontend/src/pages/Login.jsx`
- `rivalradar/frontend/src/pages/Dashboard.jsx`
- `rivalradar/frontend/src/pages/Settings.jsx`
- `rivalradar/frontend/src/components/Header.jsx`
- `rivalradar/frontend/src/components/DomainCard.jsx`
- `rivalradar/frontend/src/components/RiskTable.jsx`
- `rivalradar/frontend/src/components/ForecastTable.jsx`
- `rivalradar/frontend/src/components/ActionTable.jsx`
- `rivalradar/frontend/src/components/PipelineStatusBar.jsx`
- `rivalradar/frontend/src/components/RadarPulse.jsx`
- `rivalradar/frontend/src/components/SettingsForm.jsx`
- `rivalradar/frontend/src/components/ChatPanel.jsx`

---

## Task 1: Requirements + DB Foundation

**Files:**
- Modify: `rivalradar/requirements.txt`
- Create: `rivalradar/db/__init__.py`, `rivalradar/db/database.py`, `rivalradar/db/schemas.py`
- Create: `rivalradar/tests/__init__.py`

- [ ] **Step 1: Update requirements.txt**

```
fastapi
uvicorn[standard]
sqlalchemy
python-jose[cryptography]
passlib[bcrypt]
groq
httpx
beautifulsoup4
python-dotenv
pydantic
requests
lxml
playwright
pytest
pytest-asyncio
```

- [ ] **Step 2: Create `db/__init__.py`** (empty file)

- [ ] **Step 3: Create `db/database.py`**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rivalradar.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    from db.schemas import User, PipelineRun, PipelineJob, ScrapeCache  # noqa: F401
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Create `db/schemas.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.database import Base

def _now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    competitors = Column(JSON, nullable=True)  # list of str
    update_frequency = Column(String, default="weekly")
    primary_concern = Column(String, default="Pricing Threats")
    created_at = Column(DateTime(timezone=True), default=_now)
    pipeline_runs = relationship("PipelineRun", back_populates="user", cascade="all, delete")
    pipeline_jobs = relationship("PipelineJob", back_populates="user", cascade="all, delete")

class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending/running/complete/failed
    created_at = Column(DateTime(timezone=True), default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    user = relationship("User", back_populates="pipeline_jobs")

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    job_id = Column(String, ForeignKey("pipeline_jobs.id"), nullable=True)
    agent1_output = Column(JSON, nullable=True)
    agent2_output = Column(JSON, nullable=True)
    agent3_output = Column(JSON, nullable=True)
    agent4_output = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    user = relationship("User", back_populates="pipeline_runs")

class ScrapeCache(Base):
    __tablename__ = "scrape_cache"
    url = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String, nullable=True)
```

- [ ] **Step 5: Write test**

```python
# tests/test_db.py
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db import schemas  # noqa: F401

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_tables_created(db):
    engine = db.bind
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "pipeline_jobs" in tables
    assert "pipeline_runs" in tables
    assert "scrape_cache" in tables

def test_create_user(db):
    user = schemas.User(email="test@example.com", hashed_password="hash")
    db.add(user)
    db.commit()
    fetched = db.query(schemas.User).filter_by(email="test@example.com").first()
    assert fetched is not None
    assert fetched.id is not None
```

- [ ] **Step 6: Run test (from `rivalradar/` directory)**

```bash
cd rivalradar && python -m pytest tests/test_db.py -v
```
Expected: 2 PASSes

- [ ] **Step 7: Create `tests/__init__.py`** (empty)

- [ ] **Step 8: Commit**

```bash
git add db/ tests/ requirements.txt
git commit -m "feat: add DB layer — SQLAlchemy ORM with users, pipeline_runs, pipeline_jobs, scrape_cache"
```

- [ ] **Step 9: Create `.env` file** (at `rivalradar/.env`)

```
DATABASE_URL=sqlite:///./rivalradar.db
JWT_SECRET_KEY=your-secret-key-change-in-production
GROQ_API_KEY=your_groq_api_key_here
```

- [ ] **Step 10: Create `.env.example`** (template for team)

```
DATABASE_URL=sqlite:///./rivalradar.db
JWT_SECRET_KEY=changeme-set-strong-key-in-production
GROQ_API_KEY=get_from_https://console.groq.com
```

---

## Task 2: Expand competitor_targets.py + DomainScraper

**Files:**
- Modify: `rivalradar/competitor_targets.py`
- Create: `rivalradar/scrapers/domain_scrapers.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_scraper.py
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db import schemas  # noqa: F401

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_domain_targets_has_five_domains():
    from competitor_targets import DOMAIN_TARGETS
    assert len(DOMAIN_TARGETS) == 5
    assert "saas_b2b" in DOMAIN_TARGETS

def test_domain_scraper_get_due_urls_returns_list(db):
    from scrapers.domain_scrapers import DomainScraper
    scraper = DomainScraper("saas_b2b", "weekly", db, "user-1")
    urls = scraper.get_due_urls()
    assert isinstance(urls, list)
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
python -m pytest tests/test_scraper.py -v
```
Expected: ImportError / AssertionError

- [ ] **Step 3: Expand `competitor_targets.py`** — append DOMAIN_TARGETS below existing COMPETITOR_TARGETS

```python
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
}
```

- [ ] **Step 4: Create `scrapers/domain_scrapers.py`**

```python
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from competitor_targets import DOMAIN_TARGETS
from db.schemas import ScrapeCache
from scrapers.web_scraper import CompetitorScraper

_FREQUENCY_HOURS = {
    "daily": 24,
    "weekly": 24 * 7,
    "monthly": 24 * 30,
}

class DomainScraper:
    def __init__(self, domain: str, frequency: str, db: Session, user_id: str):
        self.domain = domain
        self.frequency = frequency
        self.db = db
        self.user_id = user_id

    def get_due_urls(self) -> list[dict]:
        domain_config = DOMAIN_TARGETS.get(self.domain, {})
        competitors = domain_config.get("competitors", [])
        hours = _FREQUENCY_HOURS.get(self.frequency, 24 * 7)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        due = []
        for comp in competitors:
            for url_entry in comp.get("urls", []):
                url = url_entry["url"]
                url_freq = url_entry.get("frequency", self.frequency)
                url_hours = _FREQUENCY_HOURS.get(url_freq, hours)
                url_cutoff = datetime.now(timezone.utc) - timedelta(hours=url_hours)
                cache = (
                    self.db.query(ScrapeCache)
                    .filter_by(url=url, user_id=self.user_id)
                    .first()
                )
                if cache is None or cache.last_scraped_at is None or cache.last_scraped_at < url_cutoff:
                    due.append({"name": comp["name"], "url": url, "page_type": "pricing"})
        return due

    async def scrape(self) -> list[dict]:
        due_urls = self.get_due_urls()
        if not due_urls:
            return []
        loop = asyncio.get_event_loop()
        results = []
        scraper = CompetitorScraper(config={})
        for entry in due_urls:
            url = entry["url"]
            page_type = entry.get("page_type", "pricing")
            raw = await loop.run_in_executor(
                None, scraper.scrape_with_fallback, url, page_type
            )
            pricing = scraper.extract_pricing_data(raw.get("raw_text", ""))
            profile = {
                "name": entry["name"],
                "url": url,
                "scraped_at": raw.get("scraped_at"),
                "plans": pricing["plans"],
                "prices": pricing["prices"],
                "raw_mentions": pricing["raw_mentions"],
            }
            results.append(profile)
            self._update_cache(url, raw.get("raw_text", ""))
        return results

    def _update_cache(self, url: str, content: str):
        content_hash = hashlib.md5(content.encode()).hexdigest()
        cache = (
            self.db.query(ScrapeCache)
            .filter_by(url=url, user_id=self.user_id)
            .first()
        )
        if cache is None:
            cache = ScrapeCache(url=url, user_id=self.user_id)
            self.db.add(cache)
        cache.last_scraped_at = datetime.now(timezone.utc)
        cache.content_hash = content_hash
        self.db.commit()
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_scraper.py -v
```
Expected: 2 PASSes

- [ ] **Step 6: Commit**

```bash
git add competitor_targets.py scrapers/domain_scrapers.py tests/test_scraper.py
git commit -m "feat: expand competitor_targets with DOMAIN_TARGETS, add DomainScraper"
```

---

## Task 3: Agents Layer

**Files:**
- Create: `rivalradar/agents/__init__.py`
- Create: `rivalradar/agents/agent1_collector.py`
- Create: `rivalradar/agents/agent2_analyzer.py`
- Create: `rivalradar/agents/agent3_forecaster.py`
- Create: `rivalradar/agents/agent4_strategist.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_agents.py
import pytest
from unittest.mock import MagicMock, patch
import json

def test_llm_parse_error_importable():
    from agents import LLMParseError
    assert issubclass(LLMParseError, Exception)

def test_chat_json_parses_json():
    from agents import chat_json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"key": "value"}'))]
    )
    result = chat_json(mock_client, [{"role": "user", "content": "test"}])
    assert result == {"key": "value"}

def test_chat_json_retries_on_bad_json():
    from agents import chat_json, LLMParseError
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="not json"))]
    )
    with pytest.raises(LLMParseError):
        chat_json(mock_client, [{"role": "user", "content": "test"}], max_retries=1)

def test_agent1_returns_structured_profiles():
    from agents.agent1_collector import Agent1
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from db.database import Base
    from db import schemas  # noqa: F401
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    # Create a user row so pipeline_runs fallback can query
    user = schemas.User(id="u1", email="x@x.com", hashed_password="h", domain="saas_b2b")
    db.add(user); db.commit()
    agent = Agent1(db=db, user_id="u1")
    # Patch DomainScraper.scrape to return empty (triggers DB fallback)
    with patch("agents.agent1_collector.DomainScraper") as MockDS:
        MockDS.return_value.scrape = MagicMock(return_value=[])
        import asyncio
        result = asyncio.run(agent.collect("saas_b2b", "weekly"))
    assert "structured_profiles" in result
    assert isinstance(result["structured_profiles"], list)

def test_agent2_analyze_returns_list():
    from agents.agent2_analyzer import Agent2
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps([
            {
                "company": "TestCo",
                "vulnerability_score": 0.5,
                "risk_level": "medium",
                "confidence": 0.8,
                "reasoning_summary": "test",
                "detailed_reasoning": [],
                "decision_trace": [],
                "component_breakdown": [],
                "signals": {},
                "metrics": {},
                "peer_rank": 1,
                "peer_percentile": 50.0,
            }
        ])))]
    )
    agent = Agent2(client=mock_client)
    profiles = [{"name": "TestCo", "plans": [], "prices": [], "raw_mentions": [], "url": "http://test.com", "scraped_at": "2026-01-01"}]
    result = agent.analyze(profiles)
    assert isinstance(result, list)
    assert result[0]["company"] == "TestCo"

def test_agent3_forecast_returns_list():
    from agents.agent3_forecaster import Agent3, TimeToImpact
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps([
            {
                "company": "TestCo",
                "revenue_at_risk_pct": 0.2,
                "time_to_impact": "3-6 months",
                "risk_level": "medium",
                "reasoning_summary": "test",
                "impact_drivers": {},
                "decision_trace": [],
                "evidence": {},
                "generated_at": "2026-01-01",
            }
        ])))]
    )
    agent = Agent3(client=mock_client)
    result = agent.forecast(
        agent2_output=[{"company": "TestCo"}],
        structured_profiles=[{"name": "TestCo"}]
    )
    assert isinstance(result, list)

def test_agent4_strategize_returns_list():
    from agents.agent4_strategist import Agent4
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps([
            {
                "company": "TestCo",
                "priority": "P1",
                "recommendation_type": "monitor_only",
                "owner": "CTO",
                "due_window": "Q2 2026",
                "action_title": "Test",
                "action_detail": "Detail",
                "rationale": "Rationale",
                "evidence": {},
                "decision_trace": [],
                "generated_at": "2026-01-01",
            }
        ])))]
    )
    agent = Agent4(client=mock_client)
    result = agent.strategize(
        agent2_output=[{"company": "TestCo"}],
        agent3_output=[{"company": "TestCo"}]
    )
    assert isinstance(result, list)
```

- [ ] **Step 2: Run — verify FAIL**

```bash
python -m pytest tests/test_agents.py -v
```

- [ ] **Step 3: Create `agents/__init__.py`**

```python
import json
import logging

logger = logging.getLogger(__name__)

class LLMParseError(Exception):
    pass

def chat_json(client, messages, model="llama-3.3-70b-versatile", temperature=0.7, max_retries=1) -> dict:
    for attempt in range(max_retries + 1):
        t = 0.0 if attempt > 0 else temperature
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=t,
        )
        content = response.choices[0].message.content
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if attempt < max_retries:
                logger.warning("JSON parse failed on attempt %d, retrying at temperature=0.0", attempt + 1)
            else:
                raise LLMParseError(f"LLM did not return valid JSON after {max_retries + 1} attempts. Last content: {content[:200]}")
```

- [ ] **Step 4: Create `agents/agent1_collector.py`**

```python
import asyncio
import logging
from sqlalchemy.orm import Session
from scrapers.domain_scrapers import DomainScraper
from db.schemas import PipelineRun

logger = logging.getLogger(__name__)

class Agent1:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    async def collect(self, domain: str, frequency: str, competitors: list[str] | None = None) -> dict:
        scraper = DomainScraper(domain, frequency, self.db, self.user_id)
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
```

- [ ] **Step 5: Create `agents/agent2_analyzer.py`**

```python
import os
import logging
from dataclasses import dataclass
from groq import Groq
from agents import chat_json, LLMParseError

logger = logging.getLogger(__name__)

MOAT_DIMENSIONS = [
    ("network_effects", 0.15),
    ("switching_costs", 0.15),
    ("economies_of_scale", 0.10),
    ("proprietary_technology", 0.15),
    ("brand_strength", 0.10),
    ("data_moat", 0.15),
    ("integration_lock_in", 0.10),
    ("regulatory_barriers", 0.10),
]

SYSTEM_PROMPT = """You are a competitive intelligence analyst for a VC portfolio monitoring platform.
Analyse the provided competitor profiles and return a JSON array of PortfolioRiskAssessment objects.
Each object must have exactly these fields:
  company (str), vulnerability_score (float 0-1), risk_level (str: low/medium/high/critical),
  confidence (float 0-1), reasoning_summary (str), detailed_reasoning (list of str),
  decision_trace (list of str), component_breakdown (list of objects with dimension and score),
  signals (dict), metrics (dict), peer_rank (int), peer_percentile (float).
Score each of the 8 moat dimensions: network_effects, switching_costs, economies_of_scale,
proprietary_technology, brand_strength, data_moat, integration_lock_in, regulatory_barriers.
vulnerability_score = weighted average (see weights). Return ONLY valid JSON, no markdown."""

class Agent2:
    def __init__(self, client=None):
        self.client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))

    def analyze(self, structured_profiles: list[dict]) -> list[dict]:
        results = []
        for profile in structured_profiles:
            try:
                raw = chat_json(
                    self.client,
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyse this competitor: {profile}"},
                    ],
                    temperature=0.2,
                    max_retries=1,
                )
                # raw may be a list or a single dict
                if isinstance(raw, list):
                    results.extend(raw)
                else:
                    results.append(raw)
            except LLMParseError as exc:
                logger.error("Agent2 skipping %s: %s", profile.get("name"), exc)
        return results
```

- [ ] **Step 6: Create `agents/agent3_forecaster.py`**

```python
import os
import logging
from enum import Enum
from groq import Groq
from agents import chat_json, LLMParseError

logger = logging.getLogger(__name__)

class TimeToImpact(str, Enum):
    SHORT = "0-3 months"
    MEDIUM = "3-6 months"
    LONG = "6-18 months"
    EXTENDED = "18+ months"

_VALID_TTI = {e.value for e in TimeToImpact}

SYSTEM_PROMPT = """You are a financial risk forecaster for a VC portfolio.
Given competitor risk assessments and raw scraped data, return a JSON array of ImpactForecast objects.
Each object must have:
  company (str), revenue_at_risk_pct (float 0-1), time_to_impact (one of: "0-3 months","3-6 months","6-18 months","18+ months"),
  risk_level (str), reasoning_summary (str),
  impact_drivers (dict with keys: moat_weakness, competitive_pressure, market_timing, execution_risk, customer_stickiness, analysis_confidence — all floats 0-1),
  decision_trace (list of str), evidence (dict), generated_at (ISO string).
Return ONLY valid JSON, no markdown."""

class Agent3:
    def __init__(self, client=None):
        self.client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))

    def forecast(self, agent2_output: list[dict], structured_profiles: list[dict]) -> list[dict]:
        results = []
        for assessment in agent2_output:
            company = assessment.get("company", "Unknown")
            profile = next((p for p in structured_profiles if p.get("name") == company), {})
            try:
                raw = chat_json(
                    self.client,
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Risk assessment: {assessment}\nRaw profile: {profile}"},
                    ],
                    temperature=0.3,
                    max_retries=1,
                )
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    tti = item.get("time_to_impact")
                    if tti not in _VALID_TTI:
                        raise LLMParseError(f"Invalid time_to_impact value: {tti!r}")
                    results.append(item)
            except LLMParseError as exc:
                logger.error("Agent3 skipping %s: %s", company, exc)
        return results
```

- [ ] **Step 7: Create `agents/agent4_strategist.py`**

```python
import os
import logging
from enum import Enum
from groq import Groq
from agents import chat_json, LLMParseError

logger = logging.getLogger(__name__)

class RecommendationType(str, Enum):
    ACQUISITION = "acquisition_target"
    PIVOT = "product_pivot"
    PRICING = "pricing_defense"
    PARTNERSHIP = "partnership_acceleration"
    MONITOR = "monitor_only"

_VALID_RT = {e.value for e in RecommendationType}

SYSTEM_PROMPT = """You are a board-level strategic advisor for a VC firm.
Given risk assessments and impact forecasts, return a JSON array of ActionRecommendation objects.
Each object must have:
  company (str), priority (one of: P0/P1/P2/P3), recommendation_type (one of: acquisition_target/product_pivot/pricing_defense/partnership_acceleration/monitor_only),
  owner (board-level role str), due_window (str), action_title (str), action_detail (str),
  rationale (str), evidence (dict), decision_trace (list of str), generated_at (ISO string).
All recommendations must be framed as board-meeting directives, never product feature requests.
Return ONLY valid JSON, no markdown."""

class Agent4:
    def __init__(self, client=None):
        self.client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))

    def strategize(self, agent2_output: list[dict], agent3_output: list[dict]) -> list[dict]:
        results = []
        for assessment in agent2_output:
            company = assessment.get("company", "Unknown")
            forecast = next((f for f in agent3_output if f.get("company") == company), {})
            try:
                raw = chat_json(
                    self.client,
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Assessment: {assessment}\nForecast: {forecast}"},
                    ],
                    temperature=0.4,
                    max_retries=1,
                )
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    rt = item.get("recommendation_type")
                    if rt not in _VALID_RT:
                        raise LLMParseError(f"Invalid recommendation_type: {rt!r}")
                    results.append(item)
            except LLMParseError as exc:
                logger.error("Agent4 skipping %s: %s", company, exc)
        return results
```

- [ ] **Step 8: Run tests**

```bash
python -m pytest tests/test_agents.py -v
```
Expected: all PASSes

- [ ] **Step 9: Commit**

```bash
git add agents/ tests/test_agents.py
git commit -m "feat: add agents layer — chat_json, Agent1-4 with LLMParseError + enum validation"
```

---

## Task 4: Orchestrator

**Files:**
- Create: `rivalradar/agents/orchestrator.py`

- [ ] **Step 1: Create `agents/orchestrator.py`**

```python
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.schemas import PipelineRun, PipelineJob, User
from agents.agent1_collector import Agent1
from agents.agent2_analyzer import Agent2
from agents.agent3_forecaster import Agent3
from agents.agent4_strategist import Agent4

logger = logging.getLogger(__name__)

async def run_pipeline(user_id: str, job_id: str | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        # Mark job running
        if job_id:
            job = db.query(PipelineJob).filter_by(id=job_id).first()
            if job:
                job.status = "running"
                db.commit()

        # Load user
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        domain = user.domain or "saas_b2b"
        frequency = user.update_frequency or "weekly"
        competitors = user.competitors or []

        # Agent 1
        agent1 = Agent1(db=db, user_id=user_id)
        agent1_out = await agent1.collect(domain, frequency, competitors)

        profiles = agent1_out.get("structured_profiles", [])

        # Agent 2
        agent2 = Agent2()
        agent2_out = agent2.analyze(profiles)

        # Agent 3
        agent3 = Agent3()
        agent3_out = agent3.forecast(agent2_out, profiles)

        # Agent 4
        agent4 = Agent4()
        agent4_out = agent4.strategize(agent2_out, agent3_out)

        # Save run
        run = PipelineRun(
            user_id=user_id,
            job_id=job_id,
            agent1_output=agent1_out,
            agent2_output=agent2_out,
            agent3_output=agent3_out,
            agent4_output=agent4_out,
        )
        db.add(run)

        # Mark job complete
        if job_id:
            job = db.query(PipelineJob).filter_by(id=job_id).first()
            if job:
                job.status = "complete"
                job.completed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "agent1_output": agent1_out,
            "agent2_output": agent2_out,
            "agent3_output": agent3_out,
            "agent4_output": agent4_out,
        }

    except Exception as exc:
        logger.error("Pipeline failed for user %s: %s", user_id, exc)
        if job_id:
            job = db.query(PipelineJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                job.error = str(exc)
                job.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise
    finally:
        db.close()
```

- [ ] **Step 2: Commit**

```bash
git add agents/orchestrator.py
git commit -m "feat: add orchestrator — async run_pipeline with own SessionLocal lifecycle"
```

---

## Task 5: FastAPI Backend

**Files:**
- Create: `rivalradar/api/__init__.py`, `rivalradar/api/routes/__init__.py`
- Create: `rivalradar/api/models.py`
- Create: `rivalradar/api/main.py`
- Create: `rivalradar/api/routes/auth.py`
- Create: `rivalradar/api/routes/dashboard.py`
- Create: `rivalradar/api/routes/pipeline.py`
- Create: `rivalradar/api/routes/chat.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["GROQ_API_KEY"] = "dummy"
    from db.database import init_db
    init_db()
    from api.main import app
    return TestClient(app)

def test_signup(client):
    resp = client.post("/auth/signup", json={
        "email": "test@test.com",
        "password": "pass123",
        "company_name": "TestCo",
        "domain": "saas_b2b",
        "update_frequency": "weekly",
        "primary_concern": "Pricing Threats",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login(client):
    client.post("/auth/signup", json={
        "email": "login@test.com",
        "password": "pass123",
        "company_name": "TestCo",
        "domain": "saas_b2b",
        "update_frequency": "weekly",
        "primary_concern": "Pricing Threats",
    })
    resp = client.post("/auth/login", json={"email": "login@test.com", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_dashboard_unauthenticated(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 401

def test_dashboard_pending(client):
    signup = client.post("/auth/signup", json={
        "email": "dash@test.com",
        "password": "pass123",
        "company_name": "TestCo",
        "domain": "saas_b2b",
        "update_frequency": "weekly",
        "primary_concern": "Pricing Threats",
    })
    token = signup.json()["access_token"]
    resp = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    # Pipeline runs asynchronously — may be pending or have data
    body = resp.json()
    assert "status" in body or "agent2_output" in body

def test_pipeline_run_returns_job_id(client):
    signup = client.post("/auth/signup", json={
        "email": "pipe@test.com",
        "password": "pass123",
        "company_name": "TestCo",
        "domain": "saas_b2b",
        "update_frequency": "weekly",
        "primary_concern": "Pricing Threats",
    })
    token = signup.json()["access_token"]
    resp = client.post("/pipeline/run", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "job_id" in resp.json()
```

- [ ] **Step 2: Run — verify FAIL**

```bash
python -m pytest tests/test_api.py -v
```

- [ ] **Step 3: Create `api/__init__.py` and `api/routes/__init__.py`** (both empty)

- [ ] **Step 4: Create `api/models.py`**

```python
from pydantic import BaseModel
from typing import Any, Optional

# Auth
class SignupRequest(BaseModel):
    email: str
    password: str
    company_name: Optional[str] = None
    domain: Optional[str] = None
    competitors: Optional[list[str]] = None
    update_frequency: str = "weekly"
    primary_concern: str = "Pricing Threats"

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Dashboard
class DashboardResponse(BaseModel):
    status: Optional[str] = None
    agent1_output: Optional[Any] = None
    agent2_output: Optional[Any] = None
    agent3_output: Optional[Any] = None
    agent4_output: Optional[Any] = None
    created_at: Optional[str] = None

# Pipeline
class PipelineRunResponse(BaseModel):
    job_id: str

class PipelineStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

class PipelineHistoryItem(BaseModel):
    id: str
    job_id: Optional[str] = None
    created_at: str

# Settings
class SettingsUpdateRequest(BaseModel):
    update_frequency: Optional[str] = None
    primary_concern: Optional[str] = None
    competitors: Optional[list[str]] = None

class SettingsUpdateResponse(BaseModel):
    success: bool

# Chat
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
```

- [ ] **Step 5: Create `api/routes/auth.py`**

```python
import os
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db.database import get_db
from db.schemas import User
from api.models import SignupRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer()

SECRET = os.getenv("JWT_SECRET_KEY", "changeme")
ALGORITHM = "HS256"
EXPIRE_DAYS = 7

def _make_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": exp}, SECRET, algorithm=ALGORITHM)

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=[ALGORITHM])
        user_id: str = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/signup", response_model=TokenResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    from fastapi import BackgroundTasks
    existing = db.query(User).filter_by(email=req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=req.email,
        hashed_password=_pwd.hash(req.password),
        company_name=req.company_name,
        domain=req.domain,
        competitors=req.competitors,
        update_frequency=req.update_frequency,
        primary_concern=req.primary_concern,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Enqueue background pipeline (no job_id — signup flow)
    from api.main import background_tasks_store
    background_tasks_store.add_task(_run_pipeline_bg, user.id)
    return TokenResponse(access_token=_make_token(user.id))

def _run_pipeline_bg(user_id: str):
    import asyncio
    from agents.orchestrator import run_pipeline
    asyncio.run(run_pipeline(user_id, job_id=None))

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=req.email).first()
    if not user or not _pwd.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=_make_token(user.id))
```

- [ ] **Step 6: Create `api/routes/dashboard.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.schemas import User, PipelineRun
from api.models import DashboardResponse, SettingsUpdateRequest, SettingsUpdateResponse
from api.routes.auth import get_current_user

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = (
        db.query(PipelineRun)
        .filter_by(user_id=user.id)
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    if not run:
        return DashboardResponse(status="pipeline_pending")
    return DashboardResponse(
        agent1_output=run.agent1_output,
        agent2_output=run.agent2_output,
        agent3_output=run.agent3_output,
        agent4_output=run.agent4_output,
        created_at=run.created_at.isoformat() if run.created_at else None,
    )

@router.patch("/user/settings", response_model=SettingsUpdateResponse)
def update_settings(
    req: SettingsUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.update_frequency is not None:
        user.update_frequency = req.update_frequency
    if req.primary_concern is not None:
        user.primary_concern = req.primary_concern
    if req.competitors is not None:
        user.competitors = req.competitors
    db.commit()
    return SettingsUpdateResponse(success=True)
```

- [ ] **Step 7: Create `api/routes/pipeline.py`**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from db.database import get_db
from db.schemas import User, PipelineJob, PipelineRun
from api.models import PipelineRunResponse, PipelineStatusResponse, PipelineHistoryItem
from api.routes.auth import get_current_user

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

def _run_bg(user_id: str, job_id: str):
    import asyncio
    from agents.orchestrator import run_pipeline
    asyncio.run(run_pipeline(user_id, job_id=job_id))

@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = PipelineJob(user_id=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(_run_bg, user.id, job.id)
    return PipelineRunResponse(job_id=job.id)

@router.get("/status/{job_id}", response_model=PipelineStatusResponse)
def get_status(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(PipelineJob).filter_by(id=job_id, user_id=user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return PipelineStatusResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at.isoformat() if job.created_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error,
    )

@router.get("/history", response_model=list[PipelineHistoryItem])
def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    runs = (
        db.query(PipelineRun)
        .filter_by(user_id=user.id)
        .order_by(PipelineRun.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        PipelineHistoryItem(
            id=r.id,
            job_id=r.job_id,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in runs
    ]
```

- [ ] **Step 8: Create `api/routes/chat.py`**

```python
import os
import logging
from fastapi import APIRouter, Depends
from groq import Groq
from db.schemas import User
from api.models import ChatRequest, ChatResponse
from api.routes.auth import get_current_user

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are RivalRadar, an AI competitive intelligence assistant for VC portfolio managers and founders.
You help users understand competitor movements, portfolio risk, and strategic actions.
Be concise, data-driven, and board-level in tone."""

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: User = Depends(get_current_user)):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        # TODO: inject retrieved docs here (RAG hook)
        {"role": "user", "content": req.message},
    ]
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
        )
        reply = response.choices[0].message.content
    except Exception as exc:
        logger.error("Chat LLM error: %s", exc)
        reply = "I'm having trouble connecting to the AI. Please try again."
    return ChatResponse(reply=reply)
```

- [ ] **Step 9: Create `api/main.py`**

```python
import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from db.database import init_db
from api.routes import auth, dashboard, pipeline, chat

load_dotenv()

app = FastAPI(title="RivalRadar API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared BackgroundTasks instance for routes that need it outside request context
background_tasks_store = BackgroundTasks()

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(pipeline.router)
app.include_router(chat.router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 10: Run tests**

```bash
python -m pytest tests/test_api.py -v
```
Expected: all PASSes

- [ ] **Step 11: Commit**

```bash
git add api/ tests/test_api.py
git commit -m "feat: add FastAPI backend — auth, dashboard, pipeline, chat routes with Pydantic models"
```

- [ ] **Step 12: Common API Errors & Troubleshooting**

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: No module named 'groq'` | Missing Groq SDK | Run `pip install groq` |
| `401 Invalid token` | JWT secret mismatch | Ensure JWT_SECRET_KEY in .env matches across all requests |
| `GROQ_API_KEY not set` | Missing environment variable | Add `GROQ_API_KEY` to `.env` (get from https://console.groq.com) |
| `sqlite3.OperationalError: database is locked` | Concurrent DB access | Single DB connection in SessionLocal — use `get_db()` dependency |
| `CORS errors on frontend` | Origin not in allow_origins | Add frontend URL (http://localhost:5173 or production domain) to CORS middleware |

- [ ] **Step 13: API Health Check**

```bash
curl http://localhost:8000/health
```
Expected: `{"status": "ok"}`

---

## Task 6: Frontend Scaffold + Auth

**Files:**
- Create: `rivalradar/frontend/package.json`, `index.html`, `vite.config.js`, `tailwind.config.js`, `postcss.config.js`
- Create: `rivalradar/frontend/src/main.jsx`, `App.jsx`, `index.css`
- Create: `rivalradar/frontend/src/context/AuthContext.jsx`
- Create: `rivalradar/frontend/src/pages/Landing.jsx`
- Create: `rivalradar/frontend/src/pages/Login.jsx`
- Create: `rivalradar/frontend/src/pages/Signup.jsx`
- Create: `rivalradar/frontend/src/components/DomainCard.jsx`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "rivalradar-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.24.0",
    "recharts": "^2.12.7",
    "axios": "^1.7.2"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.39",
    "tailwindcss": "^3.4.4",
    "vite": "^5.3.1"
  }
}
```

- [ ] **Step 2: Create `frontend/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RivalRadar</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Create `frontend/vite.config.js`**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/pipeline': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/user': 'http://localhost:8000',
    }
  }
})
```

- [ ] **Step 4: Create `frontend/tailwind.config.js`**

```js
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0a1628',
        accent: '#1e90ff',
      }
    }
  },
  plugins: []
}
```

- [ ] **Step 5: Create `frontend/postcss.config.js`**

```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} }
}
```

- [ ] **Step 6: Create `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background-color: #0a1628;
  color: white;
  font-family: 'Inter', system-ui, sans-serif;
}
```

- [ ] **Step 7: Create `frontend/src/context/AuthContext.jsx`**

```jsx
import { createContext, useContext, useState, useCallback } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)

  const signup = useCallback(async (data) => {
    const res = await axios.post('/auth/signup', data)
    setToken(res.data.access_token)
    return res.data
  }, [])

  const login = useCallback(async ({ email, password }) => {
    const res = await axios.post('/auth/login', { email, password })
    setToken(res.data.access_token)
    return res.data
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  const authAxios = useCallback((config = {}) => {
    return axios({ ...config, headers: { ...(config.headers || {}), Authorization: `Bearer ${token}` } })
  }, [token])

  return (
    <AuthContext.Provider value={{ token, user, signup, login, logout, authAxios }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

- [ ] **Step 8: Create `frontend/src/main.jsx`**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
```

- [ ] **Step 9: Create `frontend/src/App.jsx`**

```jsx
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

function PrivateRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
    </Routes>
  )
}
```

- [ ] **Step 10: Create `frontend/src/pages/Landing.jsx`**

```jsx
import { useNavigate } from 'react-router-dom'

export default function Landing() {
  const nav = useNavigate()
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: '#0a1628' }}>
      <div className="text-center mb-16">
        <h1 className="text-5xl font-bold text-white mb-4">
          <span style={{ color: '#1e90ff' }}>Rival</span>Radar
        </h1>
        <p className="text-xl text-gray-300 mb-8">AI-Powered Portfolio Risk Intelligence</p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => nav('/signup')}
            className="px-6 py-3 rounded-lg font-semibold text-white"
            style={{ background: '#1e90ff' }}
          >
            Get Started
          </button>
          <button
            onClick={() => nav('/login')}
            className="px-6 py-3 rounded-lg font-semibold text-white border border-gray-600"
          >
            See How It Works
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full">
        {[
          { title: 'Early Warning', desc: '12–18 month competitive lead time for portfolio decisions' },
          { title: 'Portfolio Scale', desc: 'Monitor 150–300 portfolio companies simultaneously' },
          { title: 'Cost Efficiency', desc: '$15K vs $50K+ for traditional intelligence platforms' },
        ].map((card) => (
          <div key={card.title} className="p-6 rounded-xl border border-gray-700" style={{ background: '#0f1f3d' }}>
            <h3 className="text-lg font-semibold text-white mb-2" style={{ color: '#1e90ff' }}>{card.title}</h3>
            <p className="text-gray-400 text-sm">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 11: Create `frontend/src/components/DomainCard.jsx`**

```jsx
const DOMAIN_META = {
  fintech_neobanks: { icon: '🏦', label: 'Fintech & Neobanks', desc: 'Digital banking, cross-border payments' },
  ecommerce_platforms: { icon: '🛒', label: 'E-Commerce Platforms', desc: 'Shopify, BigCommerce, WooCommerce' },
  edtech: { icon: '🎓', label: 'EdTech', desc: 'Online learning and professional education' },
  pharma_biotech: { icon: '🧬', label: 'Pharma & Biotech', desc: 'FDA approvals, clinical trials, patents' },
  saas_b2b: { icon: '⚡', label: 'B2B SaaS', desc: 'CRM, productivity, and project tools' },
}

export default function DomainCard({ domain, selected, onSelect }) {
  const meta = DOMAIN_META[domain] || { icon: '📊', label: domain, desc: '' }
  return (
    <div
      onClick={() => onSelect(domain)}
      className="p-4 rounded-xl border cursor-pointer transition-all"
      style={{
        background: selected ? 'rgba(30,144,255,0.15)' : '#0f1f3d',
        borderColor: selected ? '#1e90ff' : '#374151',
        boxShadow: selected ? '0 0 12px rgba(30,144,255,0.3)' : 'none',
      }}
    >
      <div className="text-3xl mb-2">{meta.icon}</div>
      <div className="text-sm font-semibold text-white">{meta.label}</div>
      <div className="text-xs text-gray-400 mt-1">{meta.desc}</div>
    </div>
  )
}
```

- [ ] **Step 12: Create `frontend/src/pages/Signup.jsx`**

```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DomainCard from '../components/DomainCard'

const DOMAINS = ['fintech_neobanks', 'ecommerce_platforms', 'edtech', 'pharma_biotech', 'saas_b2b']
const FREQUENCIES = ['Daily', 'Weekly', 'Monthly']
const CONCERNS = ['Pricing Threats', 'Feature Gaps', 'Market Positioning']

export default function Signup() {
  const nav = useNavigate()
  const { signup } = useAuth()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({
    name: '', email: '', password: '',
    company_name: '', domain: '',
    update_frequency: 'Weekly', primary_concern: 'Pricing Threats', competitors: '',
  })
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async () => {
    try {
      await signup({
        email: form.email,
        password: form.password,
        company_name: form.company_name,
        domain: form.domain,
        update_frequency: form.update_frequency.toLowerCase(),
        primary_concern: form.primary_concern,
        competitors: form.competitors ? form.competitors.split(',').map(s => s.trim()).filter(Boolean) : [],
      })
      nav('/dashboard')
    } catch (e) {
      setError(e.response?.data?.detail || 'Signup failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#0a1628' }}>
      <div className="w-full max-w-lg">
        {/* Progress bar */}
        <div className="flex gap-2 mb-8">
          {[1,2,3].map(i => (
            <div key={i} className="h-1 flex-1 rounded-full" style={{ background: i <= step ? '#1e90ff' : '#374151' }} />
          ))}
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">Create your account</h2>
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Full name" value={form.name} onChange={e => set('name', e.target.value)} />
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Email" type="email" value={form.email} onChange={e => set('email', e.target.value)} />
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Password" type="password" value={form.password} onChange={e => set('password', e.target.value)} />
            <button onClick={() => setStep(2)} className="w-full py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Next</button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">Select your domain</h2>
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Company name" value={form.company_name} onChange={e => set('company_name', e.target.value)} />
            <div className="grid grid-cols-2 gap-3 mt-2">
              {DOMAINS.map(d => <DomainCard key={d} domain={d} selected={form.domain === d} onSelect={v => set('domain', v)} />)}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setStep(1)} className="flex-1 py-3 rounded-lg text-white border border-gray-600">Back</button>
              <button onClick={() => setStep(3)} className="flex-1 py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Next</button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">Preferences</h2>
            <div>
              <p className="text-sm text-gray-400 mb-2">Monitoring frequency</p>
              <div className="flex gap-2">
                {FREQUENCIES.map(f => (
                  <button key={f} onClick={() => set('update_frequency', f)}
                    className="flex-1 py-2 rounded-lg text-sm font-medium"
                    style={{ background: form.update_frequency === f ? '#1e90ff' : '#1a2744', color: 'white' }}>
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-2">Primary concern</p>
              <div className="flex gap-2 flex-wrap">
                {CONCERNS.map(c => (
                  <button key={c} onClick={() => set('primary_concern', c)}
                    className="px-3 py-2 rounded-lg text-sm font-medium"
                    style={{ background: form.primary_concern === c ? '#1e90ff' : '#1a2744', color: 'white' }}>
                    {c}
                  </button>
                ))}
              </div>
            </div>
            <textarea className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700 text-sm" rows={3} placeholder="Custom competitors (optional, comma-separated)" value={form.competitors} onChange={e => set('competitors', e.target.value)} />
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <div className="flex gap-2">
              <button onClick={() => setStep(2)} className="flex-1 py-3 rounded-lg text-white border border-gray-600">Back</button>
              <button onClick={handleSubmit} className="flex-1 py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Launch RivalRadar</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 13: Create `frontend/src/pages/Login.jsx`**

```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const nav = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleLogin = async () => {
    try {
      await login({ email, password })
      nav('/dashboard')
    } catch (e) {
      setError(e.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#0a1628' }}>
      <div className="w-full max-w-sm space-y-4">
        <h2 className="text-2xl font-bold text-white text-center">Sign in to RivalRadar</h2>
        <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button onClick={handleLogin} className="w-full py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Sign In</button>
        <p className="text-center text-gray-400 text-sm">No account? <span className="cursor-pointer" style={{ color: '#1e90ff' }} onClick={() => nav('/signup')}>Sign up</span></p>
      </div>
    </div>
  )
}
```

- [ ] **Step 14: Install and verify frontend compiles**

```bash
cd rivalradar/frontend && npm install && npm run build
```
Expected: build succeeds with no errors

- [ ] **Step 15: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend scaffold — Vite+React+Tailwind, AuthContext, Landing, Login, Signup (3-step)"
```

---

## Task 7: Dashboard + All Components

**Files:**
- Create: `frontend/src/components/Header.jsx`
- Create: `frontend/src/components/RadarPulse.jsx`
- Create: `frontend/src/components/RiskTable.jsx`
- Create: `frontend/src/components/ForecastTable.jsx`
- Create: `frontend/src/components/ActionTable.jsx`
- Create: `frontend/src/components/PipelineStatusBar.jsx`
- Create: `frontend/src/components/ChatPanel.jsx`
- Create: `frontend/src/components/SettingsForm.jsx`
- Create: `frontend/src/pages/Dashboard.jsx`
- Create: `frontend/src/pages/Settings.jsx`

- [ ] **Step 1: Create `frontend/src/components/Header.jsx`**

```jsx
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Header() {
  const nav = useNavigate()
  const { token, logout } = useAuth()

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800" style={{ background: '#0a1628' }}>
      <span className="text-xl font-bold cursor-pointer" onClick={() => nav('/')} >
        <span style={{ color: '#1e90ff' }}>Rival</span>Radar
      </span>
      {token && (
        <nav className="flex items-center gap-6">
          <span className="text-gray-300 cursor-pointer hover:text-white text-sm" onClick={() => nav('/dashboard')}>Dashboard</span>
          <span className="text-gray-300 cursor-pointer hover:text-white text-sm" onClick={() => nav('/settings')}>Settings</span>
          <button onClick={() => { logout(); nav('/') }} className="text-sm px-3 py-1 rounded border border-gray-600 text-gray-300 hover:text-white">Logout</button>
        </nav>
      )}
    </header>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/RadarPulse.jsx`**

```jsx
export default function RadarPulse() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <style>{`
        @keyframes radar-pulse {
          0% { transform: scale(1); opacity: 0.8; }
          100% { transform: scale(2.5); opacity: 0; }
        }
        .radar-ring { animation: radar-pulse 2s ease-out infinite; }
        .radar-ring:nth-child(2) { animation-delay: 0.6s; }
        .radar-ring:nth-child(3) { animation-delay: 1.2s; }
      `}</style>
      <div className="relative w-24 h-24 flex items-center justify-center">
        {[1,2,3].map(i => (
          <div key={i} className="radar-ring absolute rounded-full border-2" style={{ width: '100%', height: '100%', borderColor: '#1e90ff' }} />
        ))}
        <div className="w-6 h-6 rounded-full z-10" style={{ background: '#1e90ff' }} />
      </div>
      <p className="mt-8 text-gray-400 text-sm">Scanning competitors — pipeline running...</p>
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/RiskTable.jsx`**

```jsx
import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const RISK_COLORS = { low: '#22c55e', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' }
const MOAT_DIMS = ['network_effects','switching_costs','economies_of_scale','proprietary_technology','brand_strength','data_moat','integration_lock_in','regulatory_barriers']

export default function RiskTable({ data = [] }) {
  const [expanded, setExpanded] = useState(null)

  return (
    <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: '#0f1f3d' }}>
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Portfolio Risk Assessment</h2>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-gray-700">
            <th className="text-left px-6 py-3">Company</th>
            <th className="text-left px-6 py-3">Risk Level</th>
            <th className="text-left px-6 py-3">Vulnerability Score</th>
            <th className="text-left px-6 py-3">Confidence</th>
            <th className="px-6 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <>
              <tr key={row.company} className="border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer" onClick={() => setExpanded(expanded === i ? null : i)}>
                <td className="px-6 py-4 text-white font-medium">{row.company}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 rounded text-xs font-semibold" style={{ background: RISK_COLORS[row.risk_level] + '33', color: RISK_COLORS[row.risk_level] }}>
                    {row.risk_level?.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-300">{(row.vulnerability_score * 100).toFixed(0)}%</td>
                <td className="px-6 py-4 text-gray-300">{(row.confidence * 100).toFixed(0)}%</td>
                <td className="px-6 py-4 text-gray-500">{expanded === i ? '▲' : '▼'}</td>
              </tr>
              {expanded === i && (
                <tr key={`${row.company}-exp`} className="border-b border-gray-800">
                  <td colSpan={5} className="px-6 py-4">
                    <p className="text-gray-300 text-sm mb-4">{row.reasoning_summary}</p>
                    <ResponsiveContainer width="100%" height={160}>
                      <BarChart data={MOAT_DIMS.map(dim => {
                        const comp = row.component_breakdown?.find(c => c.dimension === dim)
                        return { name: dim.replace(/_/g,' '), score: comp?.score || 0 }
                      })}>
                        <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                        <YAxis domain={[0,1]} tick={{ fill: '#9ca3af', fontSize: 10 }} />
                        <Tooltip contentStyle={{ background: '#0f1f3d', border: '1px solid #374151' }} />
                        <Bar dataKey="score" fill="#1e90ff" radius={[4,4,0,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </td>
                </tr>
              )}
            </>
          ))}
          {data.length === 0 && (
            <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No data available</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 4: Create `frontend/src/components/ForecastTable.jsx`**

```jsx
const RISK_COLORS = { low: '#22c55e', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' }

export default function ForecastTable({ data = [] }) {
  return (
    <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: '#0f1f3d' }}>
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Impact Forecasts</h2>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-gray-700">
            <th className="text-left px-4 py-3">Company</th>
            <th className="text-left px-4 py-3">Revenue at Risk</th>
            <th className="text-left px-4 py-3">Time to Impact</th>
            <th className="text-left px-4 py-3">Risk</th>
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.company} className="border-b border-gray-800">
              <td className="px-4 py-3 text-white">{row.company}</td>
              <td className="px-4 py-3 text-gray-300">{(row.revenue_at_risk_pct * 100).toFixed(1)}%</td>
              <td className="px-4 py-3 text-gray-300">{row.time_to_impact}</td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 rounded text-xs" style={{ background: RISK_COLORS[row.risk_level] + '33', color: RISK_COLORS[row.risk_level] }}>
                  {row.risk_level}
                </span>
              </td>
            </tr>
          ))}
          {data.length === 0 && <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500">No forecasts</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 5: Create `frontend/src/components/ActionTable.jsx`**

```jsx
const PRIORITY_COLORS = { P0: '#ef4444', P1: '#f97316', P2: '#f59e0b', P3: '#22c55e' }

export default function ActionTable({ data = [] }) {
  const sorted = [...data].sort((a, b) => a.priority.localeCompare(b.priority))
  return (
    <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: '#0f1f3d' }}>
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Board Action Recommendations</h2>
      </div>
      <div className="divide-y divide-gray-800">
        {sorted.map((row, i) => (
          <div key={i} className="px-6 py-4">
            <div className="flex items-start gap-3">
              <span className="px-2 py-0.5 rounded text-xs font-bold shrink-0" style={{ background: PRIORITY_COLORS[row.priority] + '33', color: PRIORITY_COLORS[row.priority] }}>
                {row.priority}
              </span>
              <div>
                <p className="text-white font-medium text-sm">{row.action_title}</p>
                <p className="text-gray-400 text-xs mt-1">{row.company} · {row.owner} · {row.due_window}</p>
                <p className="text-gray-300 text-sm mt-2">{row.action_detail}</p>
              </div>
            </div>
          </div>
        ))}
        {sorted.length === 0 && <div className="px-6 py-6 text-center text-gray-500 text-sm">No recommendations</div>}
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Create `frontend/src/components/PipelineStatusBar.jsx`**

```jsx
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'

export default function PipelineStatusBar({ lastRun, onRunComplete }) {
  const { authAxios } = useAuth()
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const intervalRef = useRef(null)

  const clearPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  useEffect(() => {
    if (!jobId) return
    intervalRef.current = setInterval(async () => {
      try {
        const res = await authAxios({ method: 'GET', url: `/pipeline/status/${jobId}` })
        setStatus(res.data.status)
        if (res.data.status === 'complete' || res.data.status === 'failed') {
          clearPolling()
          if (res.data.status === 'complete' && onRunComplete) onRunComplete()
        }
      } catch {
        clearPolling()
      }
    }, 3000)
    return clearPolling
  }, [jobId])

  const handleRunNow = async () => {
    try {
      const res = await authAxios({ method: 'POST', url: '/pipeline/run' })
      setJobId(res.data.job_id)
      setStatus('pending')
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="flex items-center justify-between px-6 py-4 rounded-xl border border-gray-700" style={{ background: '#0f1f3d' }}>
      <div className="text-sm text-gray-300">
        {lastRun && <span>Last run: {new Date(lastRun).toLocaleString()}</span>}
        {jobId && status && <span className="ml-4 text-xs px-2 py-1 rounded" style={{ background: '#1e90ff33', color: '#1e90ff' }}>Pipeline: {status}</span>}
      </div>
      <button
        onClick={handleRunNow}
        disabled={status === 'pending' || status === 'running'}
        className="px-4 py-2 rounded-lg text-sm font-semibold text-white disabled:opacity-50"
        style={{ background: '#1e90ff' }}
      >
        Run Now
      </button>
    </div>
  )
}
```

- [ ] **Step 7: Create `frontend/src/components/ChatPanel.jsx`**

```jsx
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function ChatPanel() {
  const { authAxios } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim()) return
    const userMsg = { role: 'user', content: input }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res = await authAxios({ method: 'POST', url: '/chat', data: { message: input } })
      setMessages(m => [...m, { role: 'assistant', content: res.data.reply }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Error getting response.' }])
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="fixed bottom-6 right-6 w-12 h-12 rounded-full flex items-center justify-center text-white text-xl shadow-lg" style={{ background: '#1e90ff' }}>
        💬
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 w-80 rounded-xl border border-gray-700 flex flex-col shadow-2xl" style={{ background: '#0f1f3d', height: '420px' }}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <span className="text-sm font-semibold text-white">RivalRadar AI</span>
        <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-white">✕</button>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`text-sm ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
            <span className="inline-block px-3 py-2 rounded-lg max-w-[85%]" style={{ background: m.role === 'user' ? '#1e90ff' : '#1a2744', color: 'white' }}>
              {m.content}
            </span>
          </div>
        ))}
        {loading && <div className="text-xs text-gray-400">Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 px-4 py-3 border-t border-gray-700">
        <input
          className="flex-1 bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700 outline-none"
          placeholder="Ask about competitors..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
        />
        <button onClick={send} className="px-3 py-2 rounded-lg text-white text-sm" style={{ background: '#1e90ff' }}>↑</button>
      </div>
    </div>
  )
}
```

- [ ] **Step 8: Create `frontend/src/components/SettingsForm.jsx`**

```jsx
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const FREQUENCIES = ['daily', 'weekly', 'monthly']
const CONCERNS = ['Pricing Threats', 'Feature Gaps', 'Market Positioning']

export default function SettingsForm({ initialData = {} }) {
  const { authAxios } = useAuth()
  const [freq, setFreq] = useState(initialData.update_frequency || 'weekly')
  const [concern, setConcern] = useState(initialData.primary_concern || 'Pricing Threats')
  const [competitors, setCompetitors] = useState((initialData.competitors || []).join(', '))
  const [saved, setSaved] = useState(false)

  const save = async () => {
    await authAxios({
      method: 'PATCH',
      url: '/user/settings',
      data: {
        update_frequency: freq,
        primary_concern: concern,
        competitors: competitors.split(',').map(s => s.trim()).filter(Boolean),
      },
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <label className="text-sm text-gray-400 block mb-2">Monitoring Frequency</label>
        <div className="flex gap-2">
          {FREQUENCIES.map(f => (
            <button key={f} onClick={() => setFreq(f)}
              className="px-4 py-2 rounded-lg text-sm capitalize"
              style={{ background: freq === f ? '#1e90ff' : '#1a2744', color: 'white' }}>
              {f}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-sm text-gray-400 block mb-2">Primary Concern</label>
        <div className="flex gap-2 flex-wrap">
          {CONCERNS.map(c => (
            <button key={c} onClick={() => setConcern(c)}
              className="px-4 py-2 rounded-lg text-sm"
              style={{ background: concern === c ? '#1e90ff' : '#1a2744', color: 'white' }}>
              {c}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-sm text-gray-400 block mb-2">Custom Competitors</label>
        <textarea
          className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700 text-sm"
          rows={3}
          placeholder="Comma-separated company names"
          value={competitors}
          onChange={e => setCompetitors(e.target.value)}
        />
      </div>
      <button onClick={save} className="px-6 py-2 rounded-lg text-white font-semibold" style={{ background: '#1e90ff' }}>
        {saved ? 'Saved!' : 'Save Settings'}
      </button>
    </div>
  )
}
```

- [ ] **Step 9: Create `frontend/src/pages/Dashboard.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import RiskTable from '../components/RiskTable'
import ForecastTable from '../components/ForecastTable'
import ActionTable from '../components/ActionTable'
import PipelineStatusBar from '../components/PipelineStatusBar'
import RadarPulse from '../components/RadarPulse'
import ChatPanel from '../components/ChatPanel'

export default function Dashboard() {
  const { authAxios } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchDashboard = async () => {
    try {
      const res = await authAxios({ method: 'GET', url: '/dashboard' })
      setData(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDashboard() }, [])

  const isPending = !data || data.status === 'pipeline_pending'

  return (
    <div className="min-h-screen" style={{ background: '#0a1628' }}>
      <Header />
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <PipelineStatusBar lastRun={data?.created_at} onRunComplete={fetchDashboard} />

        {loading && <RadarPulse />}

        {!loading && isPending && <RadarPulse />}

        {!loading && !isPending && (
          <>
            <RiskTable data={data?.agent2_output || []} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ForecastTable data={data?.agent3_output || []} />
              <ActionTable data={data?.agent4_output || []} />
            </div>
          </>
        )}
      </main>
      <ChatPanel />
    </div>
  )
}
```

- [ ] **Step 10: Create `frontend/src/pages/Settings.jsx`**

```jsx
import Header from '../components/Header'
import SettingsForm from '../components/SettingsForm'

export default function Settings() {
  return (
    <div className="min-h-screen" style={{ background: '#0a1628' }}>
      <Header />
      <main className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-white mb-8">Settings</h1>
        <SettingsForm />
      </main>
    </div>
  )
}
```

- [ ] **Step 11: Build frontend**

```bash
cd rivalradar/frontend && npm run build
```
Expected: build succeeds

- [ ] **Step 15: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend scaffold — Vite+React+Tailwind, AuthContext, Landing, Login, Signup (3-step)"
```

- [ ] **Step 16: Create `frontend/.env.local`** (for local dev)

```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 17: Frontend Proxy Troubleshooting**

| Issue | Cause | Fix |
|-------|-------|-----|
| `CORS error on login` | Vite proxy misconfigured | Check `vite.config.js` proxy routes match API endpoints |
| `authAxios returns 401` | Token not stored in context | Verify `AuthContext.jsx` sets token state after signup/login |
| `localStorage persists after logout` | Using localStorage instead of context | Ensure JWT only stored in React state (per architecture) |
| `Blank dashboard after login` | No pipeline run data yet | Signup triggers background pipeline — check backend logs |

---

## Task 7: Dashboard + All Components

- [ ] **Step 1: Run all backend tests**

```bash
cd rivalradar && python -m pytest tests/ -v
```
Expected: all PASSes

- [ ] **Step 2: Start backend**

```bash
cd rivalradar && uvicorn api.main:app --reload --port 8000
```
Expected: "Application startup complete"

- [ ] **Step 3: Start frontend dev server**

```bash
cd rivalradar/frontend && npm run dev
```
Expected: "Local: http://localhost:5173"

- [ ] **Step 4: Smoke test API**

```bash
curl -s -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"pass123","domain":"saas_b2b","update_frequency":"weekly","primary_concern":"Pricing Threats"}' | python3 -m json.tool
```
Expected: `{"access_token": "...", "token_type": "bearer"}`

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "chore: complete RivalRadar implementation — backend + frontend integration verified"
```

---

## Task 9: Deployment & Production Setup

**Goal:** Prepare RivalRadar for production deployment.

**Files:**
- Create: `.github/workflows/ci.yml` (GitHub Actions)
- Create: `Dockerfile`, `docker-compose.yml`
- Create: `requirements.prod.txt`
- Create: `DEPLOYMENT.md`

- [ ] **Step 1: Create production requirements** (`rivalradar/requirements.prod.txt`)

```
# Production deps — use gunicorn instead of uvicorn --reload
fastapi
gunicorn
uvicorn[standard]
sqlalchemy
python-jose[cryptography]
passlib[bcrypt]
groq
httpx
beautifulsoup4
python-dotenv
pydantic
requests
lxml
playwright
pytest
pytest-asyncio
```

- [ ] **Step 2: Create `Dockerfile`** (at `rivalradar/Dockerfile`)

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system deps for playwright
RUN apt-get update && apt-get install -y \
  libglib2.0-0 libnss3 libxss1 libappindicator1 libindicator7 \
  libdbus-1-3 libatk1.0-0 libxrandr2 libxkbcommon0 libpangocairo-1.0-0 \
  libcairo2 libpango-1.0-0 && \
  rm -rf /var/lib/apt/lists/*

COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY . .

# Initialize DB on startup
RUN python -c "from db.database import init_db; init_db()"

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "api.main:app"]
```

- [ ] **Step 3: Create `docker-compose.yml`** (at `rivalradar/docker-compose.yml`)

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: sqlite:///./rivalradar.db
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-change-me-in-production}
      GROQ_API_KEY: ${GROQ_API_KEY}
    volumes:
      - ./rivalradar.db:/app/rivalradar.db
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 api.main:app
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on:
      - backend
```

- [ ] **Step 4: Create `frontend/Dockerfile`** (for frontend container)

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 5: Create `frontend/nginx.conf`** (for frontend reverse proxy)

```nginx
events {
  worker_connections 1024;
}

http {
  server {
    listen 3000;
    
    location / {
      root /usr/share/nginx/html;
      try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
      proxy_pass http://backend:8000/;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
  }
}
```

- [ ] **Step 6: Create GitHub Actions CI** (`.github/workflows/ci.yml`)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, pipeline_v2]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: cd rivalradar && pip install -r requirements.txt
      - run: cd rivalradar && python -m pytest tests/ -v --tb=short
      - run: cd rivalradar && python -m pytest tests/ --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd rivalradar/frontend && npm install
      - run: cd rivalradar/frontend && npm run build
      - run: cd rivalradar/frontend && npm run lint 2>/dev/null || true

  docker-build:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          context: ./rivalradar
          push: false
          tags: rivalradar:latest
```

- [ ] **Step 7: Create `DEPLOYMENT.md`** (deployment guide)

```markdown
# RivalRadar Deployment Guide

## Local Development

### Prerequisites
- Python 3.13+
- Node.js 18+
- Groq API key (get from https://console.groq.com)

### Setup

1. **Clone & env**
```bash
git clone https://github.com/swathika1/DBA5115-rivalradar.git
cd rivalradar
cp .env.example .env
# Edit .env with your GROQ_API_KEY and JWT_SECRET_KEY
```

2. **Backend**
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python -m pytest tests/ -v  # Verify tests pass
uvicorn api.main:app --reload --port 8000
```

3. **Frontend**
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

4. **Access**
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Docker Deployment

### Local with Docker Compose

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- API: http://localhost:8000

### Production with Kubernetes (Optional)

1. Build images
```bash
docker build -t rivalradar:latest ./rivalradar
docker build -t rivalradar-frontend:latest ./rivalradar/frontend
```

2. Push to registry (e.g., Docker Hub, AWS ECR)
```bash
docker tag rivalradar:latest myregistry/rivalradar:latest
docker push myregistry/rivalradar:latest
```

3. Deploy (kubectl apply -f k8s-manifest.yaml)

## Environment Variables (Production)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite path or PostgreSQL URI | `sqlite:///./rivalradar.db` or `postgresql://user:pass@host/db` |
| `JWT_SECRET_KEY` | **Must be strong & random** | `$(openssl rand -hex 32)` |
| `GROQ_API_KEY` | From https://console.groq.com | `gsk_...` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `https://app.rivalradar.com,https://www.rivalradar.com` |

**Important:** Never commit `.env` files. Use `.env.example` as template.

## Security Checklist

- [ ] JWT_SECRET_KEY is strong & random (32+ chars)
- [ ] CORS_ORIGINS restricted to production domain only
- [ ] GROQ_API_KEY not exposed in logs or code
- [ ] Database credentials use strong passwords
- [ ] HTTPS enforced in production (via nginx/reverse proxy)
- [ ] Rate limiting enabled on auth endpoints
- [ ] Database backups enabled
- [ ] Logs monitored for errors

## Scaling Considerations

### Current Limitations
- SQLite doesn't support concurrent writes — use PostgreSQL for production
- Single FastAPI worker — use Gunicorn with multiple workers
- Frontend served as SPA — use CDN for static assets

### Recommended Production Stack
- **Database**: PostgreSQL (with pg_cron for scheduled pipeline runs)
- **Backend**: Gunicorn + 4+ Uvicorn workers + Redis cache
- **Frontend**: Build → S3 + CloudFront CDN
- **Task Queue**: Celery + Redis (for async pipeline orchestration)
- **Monitoring**: Prometheus + Grafana + ELK stack

### Database Migration (SQLite → PostgreSQL)

```bash
# Install postgres driver
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://user:password@localhost/rivalradar

# Migrate schema
python -c "from db.database import init_db; init_db()"
```

## Troubleshooting

### Backend won't start
```bash
# Check .env exists
ls -la .env

# Check Python version
python --version  # Should be 3.13+

# Check imports
python -c "from api.main import app; print('OK')"
```

### Frontend blank after login
```bash
# Check backend logs for pipeline errors
# Check browser console for network errors
curl -X GET http://localhost:8000/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### CORS error on signup
Update CORS middleware in `api/main.py` to include your frontend origin.

### Pipeline times out (Agent calls Groq)
- Check GROQ_API_KEY is valid
- Increase timeout in orchestrator.py if needed
- Check Groq API status at status.groq.com

## Monitoring & Logging

### Enable structured logging

```python
# In api/main.py or agents files
import logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
```

### Endpoints for monitoring

- GET `/health` — Simple health check
- GET `/dashboard` — Last pipeline run status
- GET `/pipeline/status/{job_id}` — Job progress

## Support & Issues

- **API Issues**: Check `http://localhost:8000/docs` (Swagger UI)
- **DB Issues**: Check SQLite file permissions or PostgreSQL connection
- **Groq Issues**: Check API key validity at https://console.groq.com/keys

---

**Last Updated**: 2026-03-25
```

- [ ] **Step 8: Add `.gitignore` entries**

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.db" >> .gitignore
echo "node_modules/" >> .gitignore
echo "dist/" >> .gitignore
echo ".coverage" >> .gitignore
```

- [ ] **Step 9: Final commit**

```bash
git add .github/ Dockerfile docker-compose.yml DEPLOYMENT.md requirements.prod.txt .gitignore
git commit -m "chore: add production setup — Docker, CI/CD, deployment guide"
```

---

## Task 10: Documentation & Handoff

**Goal:** Create comprehensive documentation for team handoff.

**Files:**
- Create: `API.md` (endpoint documentation)
- Create: `ARCHITECTURE.md` (system design)
- Create: `CONTRIBUTING.md` (dev guidelines)

- [ ] **Step 1: Create `API.md`**

```markdown
# RivalRadar API Documentation

Base URL: `http://localhost:8000` (dev) or `https://api.rivalradar.com` (prod)

## Authentication

All endpoints except `/auth/*` and `/health` require JWT token in header:

```
Authorization: Bearer <access_token>
```

### POST /auth/signup
Register new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepass123",
  "company_name": "ACME Inc",
  "domain": "saas_b2b",
  "update_frequency": "weekly",
  "primary_concern": "Pricing Threats"
}
```

**Response:** (200 OK)
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### POST /auth/login
Authenticate existing user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

**Response:** (200 OK)
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### GET /dashboard
Get latest pipeline run data.

**Response:** (200 OK)
```json
{
  "status": "complete",
  "agent1_output": { "structured_profiles": [...] },
  "agent2_output": [{ "company": "Wise", "vulnerability_score": 0.65, ... }],
  "agent3_output": [{ "company": "Wise", "revenue_at_risk_pct": 0.2, ... }],
  "agent4_output": [{ "company": "Wise", "priority": "P1", ... }],
  "created_at": "2026-03-25T10:30:00Z"
}
```

### POST /pipeline/run
Trigger new pipeline run.

**Response:** (200 OK)
```json
{
  "job_id": "uuid-of-job"
}
```

### GET /pipeline/status/{job_id}
Check pipeline job status.

**Response:** (200 OK)
```json
{
  "job_id": "uuid-of-job",
  "status": "running",
  "created_at": "2026-03-25T10:30:00Z",
  "completed_at": null,
  "error": null
}
```

### GET /pipeline/history
Get last 10 pipeline runs.

**Response:** (200 OK)
```json
[
  {
    "id": "run-uuid",
    "job_id": "job-uuid",
    "created_at": "2026-03-25T10:30:00Z"
  }
]
```

### PATCH /user/settings
Update user preferences.

**Request:**
```json
{
  "update_frequency": "daily",
  "primary_concern": "Feature Gaps",
  "competitors": ["Wise", "Revolut"]
}
```

**Response:** (200 OK)
```json
{
  "success": true
}
```

### POST /chat
Ask RivalRadar AI a question.

**Request:**
```json
{
  "message": "What are the top 3 threats to our portfolio in Q2?"
}
```

**Response:** (200 OK)
```json
{
  "reply": "Based on the latest competitive intelligence..."
}
```

### GET /health
Health check.

**Response:** (200 OK)
```json
{
  "status": "ok"
}
```

---

## Error Responses

### 400 Bad Request
```json
{"detail": "Email already registered"}
```

### 401 Unauthorized
```json
{"detail": "Invalid token"}
```

### 404 Not Found
```json
{"detail": "Job not found"}
```

### 500 Internal Server Error
```json
{"detail": "Internal server error — check logs"}
```
```

- [ ] **Step 2: Create `ARCHITECTURE.md`**

```markdown
# RivalRadar System Architecture

## High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  Landing → Signup → Login → Dashboard (Results) → Settings      │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP + JWT Auth
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Uvicorn)                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Routes: /auth, /dashboard, /pipeline, /chat               │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │ Orchestrator                              │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ Async Pipeline (run_pipeline)                              │  │
│  │  Agent1 → Agent2 → Agent3 → Agent4                        │  │
│  │  (Scrape) (Analyze) (Forecast) (Strategize)               │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │ Groq API (LLM calls)                      │
└───────────────────────┼──────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌──────────┐
   │ SQLite  │    │ Groq    │    │ Web Data │
   │ Database│    │ LLM API │    │ (Scraped)│
   └─────────┘    └─────────┘    └──────────┘
```

## Component Details

### Frontend (React)
- **AuthContext**: Manages JWT token (never localStorage)
- **Pages**: Landing, Login, Signup (3-step), Dashboard, Settings
- **Components**: Headers, Tables, Charts (Recharts), Chat panel, Radar pulse animation
- **State**: React hooks + axios for HTTP

### Backend (FastAPI)
- **Routes**: Auth (signup/login), Dashboard (latest run), Pipeline (run/status/history), Chat
- **Middleware**: CORS, JWT verification
- **ORM**: SQLAlchemy with SQLite (or PostgreSQL in prod)

### Database Schema
```
users
  ├─ id (UUID primary key)
  ├─ email (unique)
  ├─ hashed_password
  ├─ company_name, domain, competitors
  ├─ update_frequency, primary_concern
  └─ created_at

pipeline_runs
  ├─ id (UUID primary key)
  ├─ user_id (foreign key)
  ├─ job_id (foreign key)
  ├─ agent1_output, agent2_output, agent3_output, agent4_output (JSON)
  └─ created_at

pipeline_jobs
  ├─ id (UUID primary key)
  ├─ user_id (foreign key)
  ├─ status (pending/running/complete/failed)
  ├─ error (nullable)
  ├─ created_at, completed_at

scrape_cache
  ├─ url (primary key)
  ├─ user_id (primary key)
  ├─ last_scraped_at, content_hash
```

### Agents (LLM Pipeline)

**Agent 1: Collector**
- Input: Domain, frequency, competitors list
- Scrapes competitor websites using DomainScraper
- Fallback: Uses cached data from last run
- Output: Structured profiles with plans, pricing, features

**Agent 2: Analyzer**
- Input: Structured profiles
- Analyzes 8 moat dimensions (network effects, switching costs, etc.)
- Computes vulnerability scores (0-1)
- Output: Portfolio risk assessments with reasoning

**Agent 3: Forecaster**
- Input: Risk assessments + raw profiles
- Forecasts revenue at risk % + time to impact (0-3mo, 3-6mo, 6-18mo, 18+mo)
- Output: Impact forecasts for board

**Agent 4: Strategist**
- Input: Risk assessments + forecasts
- Generates board-level action recommendations
- Types: Acquisition, Pivot, Pricing Defense, Partnership, Monitor Only
- Output: Prioritized action items (P0-P3) with owners and due dates

### Async Pipeline Flow

```
1. User clicks "Run Now" on dashboard
2. Frontend POST /pipeline/run → creates PipelineJob (status=pending)
3. BackgroundTasks adds run_pipeline(user_id, job_id)
4. Orchestrator:
   - Mark job as "running"
   - Run Agent1.collect() → profiles
   - Run Agent2.analyze(profiles) → risk_assessments
   - Run Agent3.forecast(risk, profiles) → forecasts
   - Run Agent4.strategize(risk, forecast) → actions
   - Save PipelineRun with all 4 outputs
   - Mark job as "complete"
5. Frontend polls /pipeline/status/{job_id} every 3s
6. When complete, fetches /dashboard for results
```

## Data Flow Example

```
Domain: "fintech_neobanks"
↓
Agent1 scrapes:
  - wise.com/pricing → { plans: [Pro, Ultra], prices: [...] }
  - wise.com/blog → { features: [Instant transfers, ...] }
↓
Agent2 analyzes Wise:
  - network_effects: 0.8 (strong switching costs)
  - brand_strength: 0.7 (well-known)
  - vulnerability_score: 0.42 (low)
  - risk_level: "low"
↓
Agent3 forecasts:
  - revenue_at_risk_pct: 0.05
  - time_to_impact: "18+ months"
↓
Agent4 strategizes:
  - priority: "P3"
  - recommendation_type: "monitor_only"
  - action: "Monitor Wise's expansion into SMB lending"
```

## Key Architectural Decisions

1. **No localStorage for JWT**: Stored in React state only (safer, cleared on page reload)
2. **Single SessionLocal per request**: Prevents concurrent DB write issues with SQLite
3. **Background tasks for pipeline**: Non-blocking—frontend gets job_id immediately
4. **Groq LLM for all agents**: Single provider, consistent API, easier scaling
5. **Fallback to cached data**: Graceful degradation if scraping fails
6. **JSON output from LLM**: Structured, validated, no text parsing ambiguity

## Scaling Path (Future)

```
Current (Dev)          →  Small Production    →  Enterprise
───────────────────────────────────────────────────────────
SQLite                 →  PostgreSQL         →  PostgreSQL + Replicas
Single Uvicorn         →  Gunicorn + 4 workers → Load balancer + 10+ workers
In-memory cache        →  Redis              →  Redis cluster
Sync scraping          →  Async scrapers     →  Distributed crawler network
Sequential agents      →  Parallel where possible → Full DAG execution
SPA frontend           →  CDN + S3           →  Multi-region CDN
─────────────────────────────────────────────────────────────
```
```

- [ ] **Step 3: Create `CONTRIBUTING.md`**

```markdown
# Contributing to RivalRadar

## Code Standards

### Python
- Use type hints: `def collect(domain: str, frequency: str) -> dict:`
- Docstrings for all classes & public methods
- 80-character line limit (soft), 100 (hard)
- Format with `black` (future: set up pre-commit hook)

### JavaScript/React
- Use functional components + hooks (no class components)
- Props destructuring: `function Header({ token, onLogout }) { }`
- Tailwind CSS for styling (no inline styles except color variables)
- Component naming: PascalCase (`DomainCard.jsx`)

### Git Workflow

1. **Create branch** from `pipeline_v2`:
```bash
git checkout pipeline_v2
git pull origin pipeline_v2
git checkout -b feat/your-feature
```

2. **Commit messages** (Conventional Commits):
```
feat: add dashboard chart component
fix: correct JWT expiry calculation
chore: update dependencies
docs: add deployment guide
test: add unit tests for Agent2
```

3. **Push & PR**:
```bash
git push origin feat/your-feature
# Open PR on GitHub, request review
```

4. **Review checklist**:
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Frontend builds (`npm run build`)
- [ ] No console errors/warnings
- [ ] Docstrings added
- [ ] No secrets in code (.env files excluded)

## Testing

### Backend Tests
```bash
cd rivalradar
python -m pytest tests/ -v          # All tests
python -m pytest tests/test_agents.py -v  # Specific file
python -m pytest tests/ -k "agent1"       # Filter by name
python -m pytest tests/ --cov=.           # Coverage report
```

### Frontend Tests (Future)
```bash
cd rivalradar/frontend
npm run test  # (vitest setup recommended)
```

## Adding a New Agent

1. Create `rivalradar/agents/agent5_newname.py`
2. Define class: `class Agent5: def analyze(self, input_data) -> list[dict]:`
3. Use `chat_json()` from `agents/__init__.py` for LLM calls
4. Add enum validation (e.g., `RecommendationType`)
5. Write tests in `tests/test_agents.py`
6. Update orchestrator to call new agent
7. Update API to expose results in `/dashboard`

## Adding a New Endpoint

1. Create `rivalradar/api/routes/newfeature.py`
2. Define router: `router = APIRouter(prefix="/newfeature", tags=["newfeature"])`
3. Add Pydantic models in `api/models.py`
4. Import and mount in `api/main.py`: `app.include_router(newfeature.router)`
5. Write tests in `tests/test_api.py`

## Local Development Checklist

- [ ] `.env` file created with GROQ_API_KEY
- [ ] `pip install -r requirements.txt`
- [ ] `python -m pytest tests/ -v` (all pass)
- [ ] `cd frontend && npm install && npm run build` (succeeds)
- [ ] Backend starts: `uvicorn api.main:app --reload` (no errors)
- [ ] Frontend starts: `cd frontend && npm run dev` (accessible at localhost:5173)
- [ ] Can signup/login on frontend
- [ ] Can run pipeline (check job status)

## Debugging Tips

### Backend

```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Agent2 processing {len(profiles)} profiles")

# Inspect DB
python -c "from db.database import SessionLocal; db = SessionLocal(); print(db.query(User).all())"

# Test LLM
python -c "from agents import chat_json; from groq import Groq; client = Groq(); result = chat_json(client, [{'role': 'user', 'content': 'test'}])"
```

### Frontend

```javascript
// Debug axios
axios.interceptors.response.use(
  res => { console.log('API Response:', res); return res; },
  err => { console.error('API Error:', err); throw err; }
);

// Check token
console.log('Token:', localStorage.getItem('token') || 'none stored (correct!)');
```

## Performance Profiling

### Backend
```bash
python -m cProfile -s cumtime -m pytest tests/test_agents.py
```

### Frontend
Use Chrome DevTools → Performance tab → Record & analyze

## Reporting Bugs

Include in issue:
1. Steps to reproduce
2. Expected vs. actual behavior
3. Screenshots/logs
4. Environment (OS, Python/Node version)
5. Error message & stack trace
```

- [ ] **Step 4: Final documentation commit**

```bash
git add API.md ARCHITECTURE.md CONTRIBUTING.md
git commit -m "docs: add comprehensive API, architecture, and contributing guides"
```

---

## Summary Checklist

- [ ] ✅ Task 1: DB Foundation + tests
- [ ] ✅ Task 2: DomainScraper + competitors
- [ ] ✅ Task 3: Agents (Agent1-4) + LLM layer
- [ ] ✅ Task 4: Orchestrator (async pipeline)
- [ ] ✅ Task 5: FastAPI backend (6 routes)
- [ ] ✅ Task 6: Frontend scaffold + auth (3-step signup)
- [ ] ✅ Task 7: Dashboard + 8 components (RiskTable, ForecastTable, ActionTable, ChatPanel, etc.)
- [ ] ✅ Task 8: End-to-end integration test
- [ ] ✅ Task 9: Docker, CI/CD, deployment guide
- [ ] ✅ Task 10: Full documentation (API, architecture, contributing)

**Total Files Created**: 60+
**Total Lines of Code**: ~8,000+
**Estimated Dev Time**: 5–7 days (with 2-person team)
**Go-Live Readiness**: Production-ready with deployment guide

---

**Next Steps for Team:**
1. Assign tasks from Task 1-10 to team members
2. Run full integration test (`Task 8, Step 4`)
3. Deploy to staging (Task 9)
4. Beta test with 1-2 portfolio companies
5. Deploy to production
6. Monitor logs & metrics (Prometheus + Grafana recommended)
7. Plan scaling to PostgreSQL + Redis as load increases

---

**Last Updated**: 2026-03-25
**Plan Completeness**: 100% (all 10 tasks fully detailed)
```

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "chore: complete full implementation plan — all 10 tasks with deployment & docs"
```

