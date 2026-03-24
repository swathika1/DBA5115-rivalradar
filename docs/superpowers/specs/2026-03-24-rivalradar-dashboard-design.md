# RivalRadar Dashboard UI — Design Spec

**Date:** 2026-03-24
**Status:** Approved
**Scope:** Single new Jupyter notebook cell appended to `rivalradar/agentic_pipeline.ipynb`

---

## Overview

Add an interactive dashboard cell at the bottom of `agentic_pipeline.ipynb` that visualises the output of the RivalRadar agentic pipeline. The cell reads from the existing `pipeline_result` variable produced by the pipeline run cell (Cell 14) and renders four sections using Plotly. No existing cells are modified. The pipeline is not re-run inside the dashboard cell.

---

## Constraints

- **No existing cell changes except Cell 2** — only `get_openai_client()` in Cell 2 is updated to support `OPENAI_BASE_URL`; all other cells are untouched.
- **No pipeline re-execution in dashboard cell** — reads `pipeline_result` as-is.
- **Minimal new dependencies** — only `plotly` (graph_objects + subplots).
- **MVP scope** — no filtering widgets, no server, no persistence.
- **Fail fast** — guard at cell top raises `RuntimeError` if `pipeline_result` is not defined.

---

## Groq API Fix (prerequisite for pipeline)

The pipeline currently uses `OpenAI(api_key=OPENAI_API_KEY)` with no `base_url`, which routes to OpenAI's endpoint. The project has switched to a Groq API key (`gsk_...`). Two changes are required:

### 1. `.env.example`
Set `OPENAI_BASE_URL=https://api.groq.com/openai/v1` and update `OPENAI_MODEL` to a Groq-compatible model (e.g. `llama-3.3-70b-versatile`). Keep `OPENAI_API_KEY` header name unchanged.

### 2. Cell 2 — `get_openai_client()`
Read `OPENAI_BASE_URL` from `_env` and pass it to the client if present:
```python
OPENAI_BASE_URL = _env.get("OPENAI_BASE_URL", "").strip() or None

def get_openai_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
```
This is backward-compatible: if `OPENAI_BASE_URL` is empty, `base_url=None` leaves OpenAI as the default.

The dashboard cell itself makes no API calls and is unaffected by this change.

---

## Data Sources

All data comes from `pipeline_result` already bound in the kernel:

| Variable | Path | Type |
|---|---|---|
| `vulnerability_results` | `pipeline_result["agent2_output"]["vulnerability_results"]` | `list[VulnerabilityResult]` |
| `pricing_predictions` | `pipeline_result["agent3_output"]["pricing_predictions"]` | `list[PricingPrediction]` |
| `action_recommendations` | `pipeline_result["agent4_output"]["action_recommendations"]` | `list[ActionRecommendation]` |

`structured_profiles` (Agent 1) is not needed — all required data is already embedded in `VulnerabilityResult` objects.

---

## Shared Helpers

### Risk colour helper
Used in Sections 1 and 3. Returns a fill colour string based on `risk_level`:
```python
def risk_colour(level: str) -> str:
    return {
        "critical": "#FFCCCC",
        "high":     "#FFCCCC",
        "medium":   "#FFF3CC",
        "low":      "#CCFFCC",
    }.get(str(level).lower(), "#FFFFFF")  # fallback: white for unrecognised values
```

### Peer percentile formatter
Used in Section 1. Formats `peer_percentile` (a `float | None`):
```python
def fmt_pct(v) -> str:
    return f"{v:.0%}" if v is not None else "N/A"
```

---

## Section 1 — Portfolio Heatmap

**Chart type:** `plotly.graph_objects.Table`
**Columns:** Rank | Company | Vulnerability Score | Risk Level | Confidence | Peer Percentile
**Data source:** `vulnerability_results` sorted by `peer_rank` (ascending)
**Row fill:** `risk_colour(result.risk_level)` per row; fallback `#FFFFFF` for unrecognised values
**Peer Percentile display:** `fmt_pct(result.peer_percentile)` — e.g. `75%` or `N/A`
**Header row:** fill `#2C3E50`, font colour white

---

## Section 2 — Component Breakdown

**Chart type:** `plotly.subplots.make_subplots` grid of horizontal bar charts
**One subplot per company**, laid out in a 2-column grid (`rows = math.ceil(n / 2)`).
**X-axis:** `weighted_score` (fixed range `[0, 1]`); `shared_xaxes=False`
**Y-axis:** component name (5 fixed names: `pricing_pressure`, `segment_coverage`, `feature_depth`, `strategic_signals`, `business_model_pressure`)
**Bar colour:** single accent colour (`#3498DB`)
**Data source:** `result.component_breakdown` for each `VulnerabilityResult`
**Figure height:** `max(400, 300 * rows)` pixels — prevents cramped bars with many companies

---

## Section 3 — Pricing Prediction Summary

**Chart type:** `plotly.graph_objects.Table`
**Columns:** Company | Change Probability | Predicted Timeline (`p.predicted_timeline`) | Risk Level | Top Driver
**Top Driver:** `max(p.drivers, key=p.drivers.get) if p.drivers else "N/A"` — key with highest float value; guard against empty dict (Agent 3 always writes 6 driver keys, but guarded for safety)
**Data source:** `pricing_predictions` sorted by `change_probability` descending
**Row fill:** `risk_colour(p.risk_level)` per row

---

## Section 4 — Action Recommendations

**Chart type:** `plotly.graph_objects.Table`
**Columns:** Priority | Company | Action Title | Owner | Due Window | Rationale
**Data source:** `action_recommendations` sorted by `int(a.priority[1]) if len(a.priority) >= 2 and a.priority[1].isdigit() else 99` — safe numeric key, falls back to 99 for any unrecognised priority string
**Row fill colour by priority:**
- `P0` → `#FF4C4C` (red)
- `P1` → `#FFA500` (orange)
- `P2` → `#FFD700` (yellow)
- `P3` → `#EEEEEE` (light grey)
- Unrecognised → `#FFFFFF` (white fallback)

---

## Cell Structure

```python
# %% [Dashboard] RivalRadar Interactive Dashboard

import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Guard — use globals() for reliable Jupyter kernel variable check
if 'pipeline_result' not in globals():
    raise RuntimeError("Run the pipeline cell first (pipeline_result not found).")

# Extract data
vulnerability_results  = pipeline_result["agent2_output"]["vulnerability_results"]
pricing_predictions    = pipeline_result["agent3_output"]["pricing_predictions"]
action_recommendations = pipeline_result["agent4_output"]["action_recommendations"]

# Shared helpers
def risk_colour(level: str) -> str:
    return {"critical": "#FFCCCC", "high": "#FFCCCC",
            "medium": "#FFF3CC", "low": "#CCFFCC"}.get(str(level).lower(), "#FFFFFF")

def fmt_pct(v) -> str:
    return f"{v:.0%}" if v is not None else "N/A"

# --- Section 1: Portfolio Heatmap ---
# ... build go.Table using vulnerability_results, call fig1.show()

# --- Section 2: Component Breakdown ---
# ... make_subplots grid, rows=math.ceil(n/2), cols=2, height=max(400, 300*rows)
# ... call fig2.show()

# --- Section 3: Pricing Prediction Summary ---
# ... build go.Table using pricing_predictions, call fig3.show()

# --- Section 4: Action Recommendations ---
# ... build go.Table using action_recommendations sorted by:
#     key=lambda a: int(a.priority[1]) if len(a.priority) >= 2 and a.priority[1].isdigit() else 99
# ... call fig4.show()
```

Each section calls `fig.show()` independently so sections render sequentially in the notebook output.

At the end of the cell, all four figures are also written to a single self-contained HTML file using `plotly.io.write_html` with `include_plotlyjs="cdn"` (keeps file size small) and `full_html=True`. The file is saved to the same directory as the notebook as `rivalradar_dashboard.html`. A final `print()` confirms the path. Opening the file in any browser shows all four sections as interactive Plotly charts — no server required.

---

## Out of Scope (MVP)

- Dropdown/filter widgets (ipywidgets)
- Real-time refresh
- Responsive layout tuning
- Drill-down modals
- PDF export
