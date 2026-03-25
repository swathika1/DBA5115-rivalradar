# RivalRadar Troubleshooting Guide

## Issue: "No Data Available" in Dashboard

### Root Causes & Solutions

### 1. **Domain Mismatch** ✅ FIXED
- **Problem**: User selects domain "CRM" but system was looking for exact matches in `DOMAIN_TARGETS`
- **Solution**: Added case-insensitive domain lookup + created "crm" mapping in `competitor_targets.py`
- **Files Updated**:
  - `agent1_collector.py`: Added `domain.lower()` normalization
  - `competitor_targets.py`: Added "crm" domain with Salesforce, HubSpot, Pipedrive URLs

### 2. **Missing Playwright Browsers** ✅ FIXED
- **Problem**: Playwright scraper needs browser binaries (Chrome, WebKit, Firefox)
- **Solution**: Installed browsers via `playwright install`
- **Command**: `source rivalr/bin/activate && playwright install`

### 3. **Timezone Comparison Error** ✅ FIXED
- **Problem**: SQLite stores naive datetimes, causing "can't compare offset-naive and offset-aware" errors
- **Solution**: Added timezone-aware comparison with fallback in `domain_scrapers.py`
- **File Updated**: `scrapers/domain_scrapers.py` - Added proper NULL and timezone handling

### 4. **Bcrypt Version Incompatibility** ✅ FIXED
- **Problem**: Passlib 1.7.4 incompatible with bcrypt 5.0.0
- **Solution**: Downgraded bcrypt to 4.3.0
- **Files Updated**: `api/routes/auth.py` - Added password truncation (bcrypt 72-byte limit)

---

## Data Flow: How the System Works

```
User Signs Up
    ↓
System creates PipelineJob (tracks execution state)
    ↓
Agent1 (Collector)
  - Loads DomainTargets based on user's domain
  - Scrapes competitor URLs using Playwright/requests
  - Returns structured competitor profiles (plans, prices, features)
    ↓
Agent2 (Analyzer) 
  - Analyzes MOAT dimensions (network effects, switching costs, etc.)
  - Scores competitive threats 0-100%
  - Returns risk assessment per competitor
    ↓
Agent3 (Forecaster)
  - Forecasts revenue-at-risk from competitive threats
  - Estimates time-to-impact (0-3mo, 3-6mo, 6-18mo, 18+mo)
  - Returns financial impact projections
    ↓
Agent4 (Strategist)
  - Generates board-level recommendations (P0-P3 priority)
  - Suggests actions: Acquire, Partner, Reprice, Monitor, Pivot
  - Returns strategic action items
    ↓
All outputs saved to PipelineRun in database
    ↓
Frontend displays: Risk tables, Forecasts, Actions, Chat
```

---

## Testing the System

### Quick End-to-End Test

```bash
# 1. Activate environment
source "/Users/hrithikkannankrishnan/Desktop/Innovation Challenge /DBA5115-rivalradar/rivalr/bin/activate"

# 2. Start backend
cd "/Users/hrithikkannankrishnan/Desktop/Innovation Challenge /DBA5115-rivalradar/rivalradar"
uvicorn api.main:app --reload --port 8000

# 3. In new terminal, start frontend
cd /path/to/rivalradar/frontend
npm run dev

# 4. Open browser
open http://localhost:5173

# 5. Sign up with test data:
# - Email: test@company.com
# - Password: TestPassword123
# - Domain: CRM  (now supports: fintech_neobanks, ecommerce_platforms, edtech, pharma_biotech, saas_b2b, crm)
# - Competitors: Salesforce, HubSpot, Pipedrive
# - Frequency: daily

# 6. Log in and click "Run Pipeline"
```

---

## Available Domains

The system now supports these competitor domains:

| Domain | Competitors | Notes |
|--------|-------------|-------|
| **crm** | Salesforce, HubSpot, Pipedrive | Sales/CRM platforms |
| **saas_b2b** | HubSpot, Notion, Linear, ClickUp, Stripe | General B2B SaaS tools |
| **fintech_neobanks** | Wise, Revolut, Mercury | Digital banking & payments |
| **ecommerce_platforms** | Shopify, BigCommerce, WooCommerce | E-commerce builders |
| **edtech** | Coursera, Udemy, LinkedIn Learning | Online education |
| **pharma_biotech** | FDA Approvals, ClinicalTrials, Google Patents | Healthcare/pharma tracking |

---

## Pipeline Execution Flow

### Backend Process

```python
# When user clicks "Run Pipeline":
1. POST /pipeline/run
   └─ Creates PipelineJob(status="pending")
   └─ Enqueues background task: run_pipeline(user_id, job_id)

2. Background Task starts:
   └─ Agent1: await scraper.scrape() → { profiles: [...] }
   └─ Agent2: await analyzer.analyze(profiles) → { risks: [...] }
   └─ Agent3: await forecaster.forecast(profiles, risks) → { forecasts: [...] }
   └─ Agent4: await strategist.strategize(...) → { actions: [...] }
   └─ Saves all outputs to PipelineRun record

3. Frontend polls /pipeline/status/{job_id}
   └─ Returns status: pending/running/complete/failed
   └─ When complete, fetches /dashboard
   └─ Displays all 4 agent outputs in tables/charts
```

### Scraper Process

```python
# Agent1 uses DomainScraper:
1. Load DOMAIN_TARGETS[domain] → get competitor URLs
2. Query ScrapeCache for each URL
   └─ If cached AND not expired → skip
   └─ If NOT cached OR expired → scrape
3. For each due URL:
   └─ Playwright fetch (JS-rendered pages)
   └─ Fallback: requests + BeautifulSoup
   └─ Extract pricing data (plans, prices, features)
   └─ Update ScrapeCache with content hash + timestamp
4. Return structured profiles
```

---

## Common Issues & Debugging

### Issue: "structured_profiles is empty"

**Solution**: The scraper is running but returns empty data.

```bash
# Debug: Check what URLs are due for scraping
python3 << 'EOF'
from db.database import SessionLocal
from scrapers.domain_scrapers import DomainScraper
from db.schemas import User

db = SessionLocal()
user = db.query(User).first()
scraper = DomainScraper("crm", "daily", db, user.id)
due_urls = scraper.get_due_urls()
print(f"URLs due for scraping: {len(due_urls)}")
for url in due_urls:
    print(f"  - {url['name']}: {url['url']}")
db.close()
EOF
```

### Issue: Playwright browser not found

```bash
# Re-install Playwright
source rivalr/bin/activate
playwright install
```

### Issue: Timezone errors in logs

These are safe warnings from bcrypt. The system handles them gracefully.

```
(trapped) error reading bcrypt version → No action needed
ValueError: password cannot be longer than 72 bytes → Fixed by password truncation
```

---

## Production Deployment

To prepare for production:

1. **Environment Variables** (.env)
   ```
   DATABASE_URL=postgresql://user:pass@localhost/rivalradar
   JWT_SECRET_KEY=<generate-strong-key>
   GROQ_API_KEY=<your-groq-api-key>
   ```

2. **Database Migration**
   ```bash
   # Migrate from SQLite to PostgreSQL
   python3 migrate_db.py
   ```

3. **Docker Deployment**
   ```bash
   docker-compose -f docker-compose.prod.yml up
   ```

4. **CI/CD Pipeline**
   - GitHub Actions workflow in `.github/workflows/ci.yml`
   - Runs tests, builds Docker images, deploys to production

---

## Support & Monitoring

### Check System Health

```bash
# Backend health
curl http://localhost:8000/health

# Database status
python3 << 'EOF'
from db.database import SessionLocal
db = SessionLocal()
print("✅ Database connected")
db.close()
EOF

# Latest pipeline run
python3 << 'EOF'
from db.database import SessionLocal
from db.schemas import PipelineRun
db = SessionLocal()
latest = db.query(PipelineRun).order_by(PipelineRun.created_at.desc()).first()
if latest:
    print(f"✅ Last run: {latest.created_at}")
    print(f"   Agent1: {bool(latest.agent1_output)}")
    print(f"   Agent2: {bool(latest.agent2_output)}")
    print(f"   Agent3: {bool(latest.agent3_output)}")
    print(f"   Agent4: {bool(latest.agent4_output)}")
db.close()
EOF
```

---

## Next Steps

- [ ] Deploy to production (AWS/GCP/Azure)
- [ ] Set up database backups
- [ ] Configure monitoring & alerts
- [ ] Add webhook notifications
- [ ] Integrate with Slack/Teams
- [ ] Create admin dashboard
- [ ] Add more competitor domains
- [ ] Implement RAG for better recommendations

