# RivalRadar Full Stack Setup Guide

This document walks through the complete implementation of RivalRadar.

## Phase 1: Environment Setup

### 1.1 Prerequisites
- Python 3.13+
- Node.js 18+
- Groq API key (from https://console.groq.com)

### 1.2 Clone & Configure

```bash
git clone https://github.com/swathika1/DBA5115-rivalradar.git
cd rivalradar

# Copy environment template
cp .env.example .env

# Edit .env with your keys
export GROQ_API_KEY="your_groq_key_here"
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
```

### 1.3 Backend Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from fastapi import FastAPI; print('✓ FastAPI ready')"
python -c "from groq import Groq; print('✓ Groq SDK ready')"
python -c "from sqlalchemy import create_engine; print('✓ SQLAlchemy ready')"
```

## Phase 2: Database & Backend

### 2.1 Initialize Database

```bash
# Create tables
python -c "from db.database import init_db; init_db(); print('✓ Database initialized')"

# Verify schema
sqlite3 rivalradar.db ".schema"
```

### 2.2 Run Tests

```bash
# All tests
python -m pytest tests/ -v

# Should see:
# tests/test_db.py::test_tables_created PASSED
# tests/test_db.py::test_create_user PASSED
```

### 2.3 Start Backend

```bash
uvicorn api.main:app --reload --port 8000

# Should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

### 2.4 Test API Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

## Phase 3: Frontend Setup

### 3.1 Install Dependencies

```bash
cd frontend
npm install

# Verify key packages
npm list react react-router-dom axios tailwindcss
```

### 3.2 Start Dev Server

```bash
npm run dev

# Should see:
#   VITE v5.x.x  ready in xxx ms
#   ➜  Local:   http://localhost:5173/
```

### 3.3 Build for Production

```bash
npm run build

# Creates dist/ folder with optimized assets
```

## Phase 4: End-to-End Testing

### 4.1 Signup Flow

```bash
# 1. Open browser: http://localhost:5173
# 2. Click "Get Started"
# 3. Fill signup form (3 steps)
# 4. Select domain: "saas_b2b"
# 5. Submit → Backend creates user + triggers pipeline
```

### 4.2 Verify Backend Processing

```bash
# Check database
sqlite3 rivalradar.db "SELECT email, domain FROM users;" 

# Check logs in terminal running uvicorn for pipeline progress
```

### 4.3 Dashboard

```bash
# After signup, should redirect to dashboard
# See:
# - Pipeline status (pending/running/complete)
# - When complete: Risk Table, Forecasts, Actions
# - Chat panel in bottom-right
```

## Phase 5: Production Deployment

### 5.1 Environment Variables

```bash
# Production .env
DATABASE_URL=postgresql://user:pass@prod-db/rivalradar  # Switch to PostgreSQL
JWT_SECRET_KEY=$(openssl rand -hex 32)
GROQ_API_KEY=your_production_key
CORS_ORIGINS=https://rivalradar.com,https://app.rivalradar.com
```

### 5.2 Docker Build

```bash
docker build -t rivalradar:latest .
docker run -e GROQ_API_KEY=$GROQ_API_KEY -p 8000:8000 rivalradar:latest
```

### 5.3 Docker Compose

```bash
docker-compose up -d
# Starts backend + frontend + PostgreSQL
```

### 5.4 Kubernetes (Optional)

See `DEPLOYMENT.md` for k8s manifests and Helm charts.

## Phase 6: Monitoring & Scaling

### 6.1 Logs

```bash
# Backend structured logs
tail -f app.log | jq .

# Monitor Groq API usage
curl https://api.groq.com/status
```

### 6.2 Database Migration

```bash
# From SQLite to PostgreSQL
export DATABASE_URL=postgresql://user:pass@localhost/rivalradar
python -c "from db.database import init_db; init_db()"
# Data migrate separately with sqlalchemy-utils or manual script
```

### 6.3 Performance

```bash
# Enable query logging
export SQLALCHEMY_ECHO=true

# Profile pipeline
python -m cProfile -s cumtime -m pytest tests/test_agents.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ImportError: No module named 'fastapi'` | Run `pip install -r requirements.txt` |
| `GROQ_API_KEY not set` | Check `.env` file and `export` if needed |
| `CORS error on frontend` | Add frontend URL to `CORS_ORIGINS` in `.env` |
| `sqlite3.OperationalError: database is locked` | Restart backend, use PostgreSQL for prod |
| `Port 8000 already in use` | Change `uvicorn` port: `--port 8001` |
| `Node modules not installed` | Run `npm install` in frontend folder |

## Architecture Checklist

- [x] Database: SQLite (dev) → PostgreSQL (prod)
- [x] Backend: FastAPI with async pipeline
- [x] Frontend: React + Vite + Tailwind
- [x] Auth: JWT in React context (never localStorage)
- [x] Agents: 4-step LLM pipeline with retry logic
- [x] Scraping: Domain + frequency-based caching
- [x] Tests: DB, Agents, API (pytest)
- [x] CI/CD: GitHub Actions ready
- [x] Docker: Backend + Frontend + DB compose

## Next Steps

1. **Beta Testing**: Invite 2-3 portfolio companies
2. **Feedback Loop**: Collect agent prompt improvements
3. **RAG Integration**: Add document retrieval to chat
4. **Celery+Redis**: Replace FastAPI BackgroundTasks for scale
5. **Monitoring**: Set up Prometheus + Grafana
6. **CDN**: Deploy frontend to Cloudflare/AWS CloudFront

---

**Questions?** Check `CONTRIBUTING.md` or reach out to the dev team.
