# RivalRadar

RivalRadar is a 4-agent pipeline for competitor monitoring and portfolio-risk actions.

## Pipeline

1. Agent 1 (Collector)
- Scrapes competitor pricing pages and builds structured profiles.
- Output: `scraper_output/*_structured.json`

2. Agent 2 (Vulnerability Analyzer - OpenAI/Azure OpenAI)
- Uses LLM reasoning to score competitor vulnerability with detailed trace.
- Output: `scraper_output/vulnerability_report.json`

3. Agent 3 (Pricing Predictor - OpenAI/Azure OpenAI)
- Predicts probability and timeline of pricing changes.
- Output: `scraper_output/pricing_predictions_report.json`

4. Agent 4 (Action Planner - OpenAI/Azure OpenAI)
- Produces prioritized VC-facing response actions.
- Output: `scraper_output/action_recommendations_report.json`

## Setup

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set either:
- `OPENAI_API_KEY` (and optional `OPENAI_MODEL`), or
- Azure OpenAI vars: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`.

## Run

```bash
python run_scrape_and_analyze.py
```

If scraping dependencies are unavailable, the notebook can still run from existing structured files.
