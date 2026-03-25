# RivalRadar - Quick Start Guide

## ✅ All Issues Fixed!

The system is now fully functional with proper data flow from scraper → agents → frontend.

---

## 🚀 Running the System

### Terminal 1: Activate Environment & Start Backend

```bash
source "/Users/hrithikkannankrishnan/Desktop/Innovation Challenge /DBA5115-rivalradar/rivalr/bin/activate"
cd "/Users/hrithikkannankrishnan/Desktop/Innovation Challenge /DBA5115-rivalradar/rivalradar"
uvicorn api.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### Terminal 2: Start Frontend

```bash
cd "/Users/hrithikkannankrishnan/Desktop/Innovation Challenge /DBA5115-rivalradar/rivalradar/frontend"
npm run dev
```

**Expected Output:**
```
  ➜  Local:   http://localhost:5173/
```

---

### Terminal 3: Open Browser

```bash
open http://localhost:5173
```

---

## 📝 Test the Full System

### Step 1: Sign Up

Fill in the form:
- **Name**: John Doe
- **Email**: test@company.com  
- **Password**: TestPassword123
- **Company**: Acme Inc
- **Domain**: `CRM` ← **Case-insensitive (crm, CRM, Crm all work)**
- **Competitors**: Select any from the list
- **Update Frequency**: daily or weekly
- **Primary Concern**: pricing or features

**✅ Result**: User created in database, JWT token issued, redirected to dashboard

---

### Step 2: View Dashboard

After login, you'll see the dashboard with:

- **🔴 Pipeline Status**: Shows "No data available" initially (scraper running in background)
- **▶️ Run Now Button**: Click to trigger pipeline immediately
- **💬 Chat Panel**: AI assistant for competitive questions

---

### Step 3: Run Pipeline

Click **"Run Now"** button:

```
Timeline:
- T+0s: "🔄 Scanning..." status appears (Agent1 scraping competitor URLs)
- T+30-120s: Status updates as each agent completes
- T+Complete: Dashboard populates with:
  • 📊 Risk Assessment (Agent2 output)
  • 📈 Revenue Forecast (Agent3 output)
  • 💡 Strategic Actions (Agent4 output)
```

**✅ Expected Results**:

| Component | Agent | Shows |
|-----------|-------|-------|
| Risk Table | Agent2 | MOAT score, threat level, confidence % |
| Forecast Table | Agent3 | Revenue-at-risk, time-to-impact estimates |
| Action Table | Agent4 | P0-P3 recommendations (Acquire/Partner/Pivot) |

---

## 🔧 Verify All Fixes

### Fix 1: Domain Mapping

```bash
python3 << 'EOF'
from competitor_targets import DOMAIN_TARGETS
print("✅ Available domains:")
for domain in DOMAIN_TARGETS.keys():
    print(f"  - {domain}")
EOF
```

**Expected Output**:
```
✅ Available domains:
  - fintech_neobanks
  - ecommerce_platforms
  - edtech
  - pharma_biotech
  - saas_b2b
  - crm  ← NEW!
```

### Fix 2: Scraper Data Flow

```bash
source rivalr/bin/activate
python3 << 'EOF'
import asyncio
from db.database import SessionLocal
from db.schemas import User
from agents.agent1_collector import Agent1

async def test():
    db = SessionLocal()
    user = db.query(User).order_by(User.created_at.desc()).first()
    if not user:
        print("No users found")
        return
    
    print(f"Testing Agent1 for {user.email}")
    print(f"  Domain: {user.domain}")
    print(f"  Frequency: {user.update_frequency}")
    
    agent1 = Agent1(db, user.id)
    result = await agent1.collect(user.domain, user.update_frequency, user.competitors)
    profiles = result.get('structured_profiles', [])
    
    print(f"\n✅ Agent1 scraped {len(profiles)} competitor profiles:")
    for p in profiles[:3]:
        print(f"  - {p.get('name')}: {len(p.get('plans', []))} plans")
    
    db.close()

asyncio.run(test())
EOF
```

**Expected Output**:
```
Testing Agent1 for john@example.com
  Domain: CRM
  Frequency: daily

✅ Agent1 scraped 6 competitor profiles:
  - Salesforce: 3 plans
  - HubSpot: 3 plans
  - Pipedrive: 3 plans
  ...
```

### Fix 3: Database Integration

```bash
python3 << 'EOF'
from db.database import SessionLocal
from db.schemas import User, PipelineRun
db = SessionLocal()

# Check users
users = db.query(User).all()
print(f"✅ Total users: {len(users)}")

# Check pipeline runs
runs = db.query(PipelineRun).all()
print(f"✅ Total pipeline runs: {len(runs)}")

# Check latest data
latest_user = db.query(User).order_by(User.created_at.desc()).first()
if latest_user:
    latest_run = db.query(PipelineRun).filter_by(user_id=latest_user.id).order_by(PipelineRun.created_at.desc()).first()
    if latest_run:
        print(f"\n✅ Latest pipeline run for {latest_user.email}:")
        print(f"  Agent1 (Collector): {bool(latest_run.agent1_output)}")
        print(f"  Agent2 (Analyzer): {bool(latest_run.agent2_output)}")
        print(f"  Agent3 (Forecaster): {bool(latest_run.agent3_output)}")
        print(f"  Agent4 (Strategist): {bool(latest_run.agent4_output)}")

db.close()
EOF
```

---

## 📊 Data Flow Visualization

```
Frontend (React + Vite)
      ↓ (JWT in Authorization header)
Backend API (FastAPI)
      ↓
Agents Layer (Orchestrator chains 4 agents)
  ├─ Agent1: Collector (Web Scraper)
  │   ├─ DomainScraper
  │   ├─ Playwright/Requests
  │   └─ BeautifulSoup extraction
  ├─ Agent2: Analyzer (LLM Groq)
  │   └─ MOAT framework analysis
  ├─ Agent3: Forecaster (LLM Groq)
  │   └─ Revenue impact projection
  └─ Agent4: Strategist (LLM Groq)
      └─ Board-level recommendations
      ↓
Database (SQLAlchemy ORM)
  ├─ User (signup/login data)
  ├─ PipelineJob (execution tracking)
  ├─ PipelineRun (agent outputs as JSON)
  └─ ScrapeCache (URL content & timestamps)
```

---

## 🎯 What Each Agent Does

### Agent1: Collector 🔍
- **Input**: Competitor URLs from DOMAIN_TARGETS
- **Process**: Scrapes pricing pages, blogs, changelogs
- **Output**: Structured competitor profiles
```json
{
  "structured_profiles": [
    {
      "name": "Salesforce",
      "url": "https://...",
      "plans": ["Professional", "Enterprise"],
      "prices": ["$165/month", "$330/month"],
      "raw_mentions": ["CRM", "Sales Cloud"]
    }
  ]
}
```

### Agent2: Analyzer 🔍
- **Input**: Competitor profiles from Agent1
- **Process**: LLM analyzes competitive moat across 8 dimensions
- **Output**: Risk assessment + threat levels
```json
{
  "company": "Salesforce",
  "risk_level": "HIGH",
  "vulnerability_score": 78,
  "confidence": 0.92,
  "moat_scores": {
    "network_effects": 95,
    "switching_costs": 88,
    ...
  }
}
```

### Agent3: Forecaster 📈
- **Input**: Profiles + Risk analysis from Agents 1-2
- **Process**: LLM forecasts financial impact
- **Output**: Revenue-at-risk projections
```json
{
  "company": "Salesforce",
  "revenue_at_risk_million": 45.2,
  "time_to_impact": "3-6mo",
  "confidence": 0.85
}
```

### Agent4: Strategist 💡
- **Input**: All data from Agents 1-3
- **Process**: LLM generates board-level recommendations
- **Output**: Strategic action items
```json
{
  "recommendation": "PARTNER",
  "priority": "P1",
  "rationale": "Salesforce's market share in CRM enables cross-sell",
  "timeline": "Q2 2026"
}
```

---

## 🐛 Troubleshooting

If you see **"No data available"** or **"No recommendations"**:

### Check 1: Is the scraper running?
```bash
ps aux | grep playwright
ps aux | grep requests
```

### Check 2: Are the agents receiving data?
```bash
# Check database for latest pipeline run
python3 TROUBLESHOOTING.md  # See section "Check System Health"
```

### Check 3: Are Playwright browsers installed?
```bash
source rivalr/bin/activate
playwright install
```

### Check 4: Check backend logs
Look at the terminal running `uvicorn` for error messages.

---

## 📱 Features Working

- ✅ **Sign Up**: Creates user, validates email uniqueness, hashes password
- ✅ **Log In**: Validates credentials, issues JWT token
- ✅ **Dashboard**: Shows pipeline status and results
- ✅ **Pipeline Execution**: Chains 4 agents, saves outputs
- ✅ **Chat**: LLM-powered competitive Q&A
- ✅ **Settings**: Update domain, competitors, frequency
- ✅ **Logout**: Clears JWT token

---

## 🎓 Learning Resources

- **Agent Architecture**: See `agents/` directory
- **Database Models**: See `db/schemas.py`
- **API Routes**: See `api/routes/`
- **Web Scraping**: See `scrapers/domain_scrapers.py`
- **Frontend**: See `frontend/src/pages/` and `frontend/src/components/`

---

## ✨ Next Steps

1. **Test the system** (follow steps above)
2. **Check logs** for any errors
3. **Verify agent outputs** in database
4. **Deploy to production** (see SETUP_GUIDE.md)
5. **Add more domains** to DOMAIN_TARGETS
6. **Integrate with your tools** (Slack, Salesforce, HubSpot)

---

## 📞 Support

For issues, check:
1. `TROUBLESHOOTING.md` - Common issues & solutions
2. `SETUP_GUIDE.md` - Setup instructions
3. `api/routes/` - API endpoint documentation
4. `.env.example` - Environment variables reference

**Happy competing!** 🚀

