# RivalRadar Full-Stack Design Spec
**Date:** 2026-03-25
**Status:** Approved

---

## 1. Overview

RivalRadar is a production-grade competitive intelligence platform for VCs and founders. It monitors competitor pages, runs a 4-agent LLM pipeline to score portfolio risk, forecast revenue impact, and generate board-level strategic recommendations. Users interact via a dark-themed React dashboard with a built-in chatbot.

---

## 2. Repository Layout

All code lives inside `rivalradar/` (which is itself a nested git repo).

```
rivalradar/
├── agents/
│   ├── __init__.py               # chat_json helper + LLMParseError exception
│   ├── agent1_collector.py
│   ├── agent2_analyzer.py
│   ├── agent3_forecaster.py
│   ├── agent4_strategist.py
│   └── orchestrator.py
├── skills/
│   ├── agent1_collector/SKILL.md
│   ├── agent2_analyzer/SKILL.md
│   ├── agent3_forecaster/SKILL.md
│   └── agent4_strategist/SKILL.md
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── routes/
│       ├── auth.py
│       ├── pipeline.py
│       ├── dashboard.py
│       └── chat.py
├── db/
│   ├── database.py
│   └── schemas.py
├── scrapers/
│   ├── __init__.py
│   ├── web_scraper.py            # existing — unchanged
│   └── domain_scrapers.py        # new — DomainScraper class
├── competitor_targets.py          # expanded: DOMAIN_TARGETS + COMPETITOR_TARGETS
├── frontend/
│   ├── src/
│   │   ├── context/AuthContext.jsx
│   │   ├── pages/
│   │   │   ├── Landing.jsx
│   │   │   ├── Signup.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── Settings.jsx
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── DomainCard.jsx
│   │       ├── RiskTable.jsx
│   │       ├── ForecastTable.jsx
│   │       ├── ActionTable.jsx
│   │       ├── PipelineStatusBar.jsx
│   │       ├── RadarPulse.jsx
│   │       ├── SettingsForm.jsx
│   │       └── ChatPanel.jsx
│   ├── index.html
│   └── package.json
├── agentic_pipeline.ipynb         # existing — reference only
├── .env
├── .env.example
└── requirements.txt
```

---

## 3. Data Flow

```
POST /auth/signup
  → create User row
  → enqueue pipeline background task

Background task: run_pipeline(user_id)
  → Agent1.collect(domain, frequency, competitors)
      → DomainScraper filters DOMAIN_TARGETS by frequency + scrape_cache DB
      → CompetitorScraper.scrape_with_fallback() per URL
      → returns structured_profiles[]
      → fallback: load last pipeline_run from DB if zero profiles
  → Agent2.analyze(structured_profiles)
      → chat_json → Groq llama-3.3-70b-versatile
      → returns PortfolioRiskAssessment[] (8-dim moat scores)
  → Agent3.forecast(agent2_output, structured_profiles)
      → chat_json → Groq
      → returns ImpactForecast[] (revenue_at_risk_pct, time_to_impact)
  → Agent4.strategize(agent2_output, agent3_output)
      → chat_json → Groq
      → returns ActionRecommendation[] (P0–P3 board directives)
  → save all 4 outputs as JSON blobs in pipeline_runs
  → mark pipeline_job as complete

GET /dashboard
  → return latest pipeline_run JSON or {"status": "pipeline_pending"}

POST /chat
  → Groq LLM with RivalRadar system prompt
  → # TODO: inject retrieved docs here (RAG hook)
  → return {"reply": str}
```

---

## 4. Agent Architecture

### Shared: `chat_json` helper (`agents/__init__.py`)

```python
def chat_json(client, messages, model="llama-3.3-70b-versatile", temperature=0.7, retries=1) -> dict:
```

- Calls `client.chat.completions.create()`
- Parses JSON from response content
- On `JSONDecodeError`: retries once with `temperature=0.0`
- On second failure: raises `LLMParseError`

All agents use Groq SDK:
```python
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
```

### Agent 1 — Collector (`agent1_collector.py`)

- **Input:** `user_id`, domain key, frequency, optional custom competitor list
- **Process:** Calls `DomainScraper` → `CompetitorScraper.scrape_with_fallback()` per URL
- **Output:** `{"structured_profiles": [...]}`
- **Fallback:** Zero profiles → load last cached `pipeline_run` from DB
- **Temperature:** 0.0 (no LLM call; pure scraping)

### Agent 2 — Analyzer (`agent2_analyzer.py`)

- **Input:** `structured_profiles`
- **Dataclass:** `PortfolioRiskAssessment` with fields:
  - `company`, `vulnerability_score` (float), `risk_level` (low/medium/high/critical)
  - `confidence` (float), `reasoning_summary` (str), `detailed_reasoning` (list)
  - `decision_trace` (list), `component_breakdown` (list of 8 `ScoreComponent`)
  - `signals` (dict), `metrics` (dict), `peer_rank` (int), `peer_percentile` (float)
- **8-dimension moat framework** (weights):
  - network_effects (0.15), switching_costs (0.15), economies_of_scale (0.10)
  - proprietary_technology (0.15), brand_strength (0.10), data_moat (0.15)
  - integration_lock_in (0.10), regulatory_barriers (0.10)
- **Temperature:** 0.2

### Agent 3 — Forecaster (`agent3_forecaster.py`)

- **Input:** Agent 2 output + Agent 1 raw profiles
- **Dataclass:** `ImpactForecast` with fields:
  - `company`, `revenue_at_risk_pct` (float 0–1), `time_to_impact` (enum)
  - `risk_level`, `reasoning_summary`, `impact_drivers` (dict of 6 floats)
  - `decision_trace` (list), `evidence` (dict), `generated_at`
- **`time_to_impact` values:** `"0-3 months"`, `"3-6 months"`, `"6-18 months"`, `"18+ months"`
- **Driver fields:** `moat_weakness`, `competitive_pressure`, `market_timing`, `execution_risk`, `customer_stickiness`, `analysis_confidence`
- **Temperature:** 0.3

### Agent 4 — Strategist (`agent4_strategist.py`)

- **Input:** Agent 2 + Agent 3 outputs
- **Dataclass:** `ActionRecommendation` with fields:
  - `company`, `priority` (P0/P1/P2/P3), `recommendation_type` (enum)
  - `owner` (board-level role), `due_window`, `action_title`, `action_detail`
  - `rationale`, `evidence` (dict), `decision_trace` (list), `generated_at`
- **`recommendation_type` values:** `acquisition_target`, `product_pivot`, `pricing_defense`, `partnership_acceleration`, `monitor_only`
- **Prompt constraint:** All recommendations framed as board-meeting directives, never product feature requests
- **Temperature:** 0.4

### Orchestrator (`orchestrator.py`)

```python
async def run_pipeline(user_id: str, db: Session) -> dict:
    # 1. Load user profile from DB
    # 2. Agent1.collect()
    # 3. Agent2.analyze(agent1_out)
    # 4. Agent3.forecast(agent2_out, agent1_out)
    # 5. Agent4.strategize(agent2_out, agent3_out)
    # 6. Save all outputs to pipeline_runs
    # 7. Return combined result dict
```

Error handling: per-company try/except in Agents 2–4; on `LLMParseError` skip company and log. Agent 1 scrape failure → DB cache fallback.

---

## 5. Scraper Layer

### `competitor_targets.py` (expanded)

Holds both:
- `COMPETITOR_TARGETS` — existing SaaS B2B list (HubSpot, Notion, Linear, ClickUp, Stripe)
- `DOMAIN_TARGETS` — dict keyed by domain name, each entry has `description` and `competitors[]`

**5 domains:**
1. `fintech_neobanks` — Wise, Revolut, Mercury
2. `ecommerce_platforms` — Shopify, BigCommerce, WooCommerce
3. `edtech` — Coursera, Udemy, LinkedIn Learning
4. `pharma_biotech` — FDA approvals, ClinicalTrials, Google Patents
5. `saas_b2b` — references `COMPETITOR_TARGETS`

Each competitor has `name` and `urls[]`, each URL tagged with `frequency` (daily/weekly/monthly).

### `scrapers/domain_scrapers.py`

```python
class DomainScraper:
    def __init__(self, domain: str, frequency: str, db: Session):
        ...
    def get_due_urls(self) -> list[dict]:
        # filter DOMAIN_TARGETS[domain] by frequency
        # check scrape_cache for last_scraped_at
        # return only URLs due for this run
    async def scrape(self) -> list[dict]:
        # call CompetitorScraper.scrape_with_fallback() per due URL
        # update scrape_cache timestamps
        # return structured profiles
```

---

## 6. FastAPI Backend

### Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/signup` | No | Create user, trigger pipeline, return JWT |
| POST | `/auth/login` | No | Verify credentials, return JWT |
| GET | `/dashboard` | Yes | Latest pipeline results or `pipeline_pending` |
| POST | `/pipeline/run` | Yes | Enqueue background job, return `job_id` |
| GET | `/pipeline/status/{job_id}` | Yes | `pending/running/complete/failed` |
| GET | `/pipeline/history` | Yes | Last 10 runs with timestamps |
| PATCH | `/user/settings` | Yes | Update frequency, primary_concern, competitors |
| POST | `/chat` | Yes | LLM chat reply (RAG hook ready) |

### Auth
- `python-jose` for JWT encoding/decoding
- `passlib[bcrypt]` for password hashing
- `get_current_user` FastAPI dependency on all protected routes
- JWT: 7-day expiry, contains `user_id`

### DB Schemas (SQLAlchemy ORM)

- **`users`:** id, email, hashed_password, company_name, domain, competitors (JSON), update_frequency, primary_concern, created_at
- **`pipeline_runs`:** id, user_id, agent1_output (JSON), agent2_output (JSON), agent3_output (JSON), agent4_output (JSON), created_at
- **`pipeline_jobs`:** id (UUID), user_id, status, created_at, completed_at, error
- **`scrape_cache`:** url (PK), last_scraped_at, content_hash

### Pydantic Models (`api/models.py`)
Every route has typed request and response models. No raw dicts returned from any endpoint.

---

## 7. Frontend

**Stack:** Vite + React + Tailwind CSS + Recharts
**Design tokens:** Background `#0a1628`, accent `#1e90ff`, white text, card-based with subtle glows
**Auth:** JWT in `AuthContext` (React context, in-memory only — never localStorage)
**No `<form>` tags:** All inputs use `onChange`/`onClick` handlers

### Pages

**Landing (`/`):**
- Hero: logo, tagline "AI-Powered Portfolio Risk Intelligence", "Get Started" + "See How It Works" buttons
- 3 value prop cards: Early Warning (12–18 month lead), Portfolio Scale (150–300 companies), Cost Efficiency ($15K vs $50K+)

**Signup (`/signup`) — 3-step:**
- Progress bar at top
- Step 1: Name, email, password
- Step 2: Company name + 5 `DomainCard` components (icon, name, one-liner; single-select, highlights blue)
- Step 3: Frequency buttons (Daily/Weekly/Monthly), primary concern buttons (Pricing Threats/Feature Gaps/Market Positioning), optional competitors textarea

**Login (`/login`):** Email, password, login button, link to signup

**Dashboard (`/dashboard`):**
- 2-column grid (desktop), single column (mobile)
- Full-width: `RiskTable` (expandable rows → 8-dim `BarChart` via Recharts)
- Left: `ForecastTable` (revenue at risk %, time-to-impact, risk badge)
- Right: `ActionTable` (P0–P3 sorted, priority badges colored)
- Full-width: `PipelineStatusBar` (last run, next run, "Run Now" button, polling `setInterval` 3s)
- `ChatPanel`: collapsible side panel, message thread, input + send, calls `POST /chat`
- If pending: full-width `RadarPulse` placeholder card

**Settings (`/settings`):** Pre-populated `SettingsForm`, calls `PATCH /user/settings`

### Components

| Component | Purpose |
|-----------|---------|
| `Header` | Logo, nav (auth-gated), user email + logout |
| `DomainCard` | Clickable domain selector card with icon |
| `RiskTable` | Portfolio risk table with expandable Recharts rows |
| `ForecastTable` | Impact forecast table |
| `ActionTable` | Action recommendations sorted P0→P3 |
| `PipelineStatusBar` | Run status, polling, Run Now button |
| `RadarPulse` | Animated CSS radar pulse for pending state |
| `SettingsForm` | User preference editor |
| `ChatPanel` | Collapsible chatbot UI panel |

---

## 8. Chatbot (Base)

- `POST /chat` accepts `{"message": str}`, returns `{"reply": str}`
- System prompt: RivalRadar-scoped competitive intelligence assistant
- LLM: Groq `llama-3.3-70b-versatile`
- `# TODO: inject retrieved docs here` comment placed before Groq call for future RAG integration
- `ChatPanel` component accepts optional `context` prop (reserved for RAG doc chunks)

---

## 9. Constraints & Quality Standards

- No hardcoded API keys anywhere
- All agents independently importable without running the full pipeline
- `chat_json` wraps all LLM calls with retry + `LLMParseError`
- All FastAPI routes have Pydantic request/response models
- JWT in React context only — never localStorage
- No `asyncio.sleep` or `time.sleep` in async paths
- No Plotly — Recharts only in frontend
- No `<form>` tags in React

---

## 10. Environment & Setup

**`.env.example`:**
```
GROQ_API_KEY=
JWT_SECRET_KEY=
DATABASE_URL=sqlite:///./rivalradar.db
```

**`requirements.txt`:**
```
fastapi
uvicorn
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
```

**Run:**
```bash
cd rivalradar
uvicorn api.main:app --reload
# in another terminal:
cd frontend && npm install && npm run dev
```
