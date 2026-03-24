# RivalRadar Dashboard UI — Design Spec

**Date:** 2026-03-24
**Status:** Approved
**Scope:** Single new Jupyter notebook cell appended to `rivalradar/agentic_pipeline.ipynb`

---

## Overview

Add an interactive dashboard cell at the bottom of `agentic_pipeline.ipynb` that visualises the output of the RivalRadar agentic pipeline. The cell reads from the existing `pipeline_result` variable produced by the pipeline run cell (Cell 14) and renders four sections using Plotly. No existing cells are modified. The pipeline is not re-run inside the dashboard cell.

---

## Constraints

- **No existing cell changes** — append only.
- **No pipeline re-execution** — reads `pipeline_result` as-is.
- **Minimal new dependencies** — only `plotly` (graph_objects + subplots).
- **MVP scope** — no filtering widgets, no server, no persistence.
- **Fail fast** — guard at cell top raises `RuntimeError` if `pipeline_result` is not defined.

---

## Data Sources

All data comes from `pipeline_result` already bound in the kernel:

| Variable | Path | Type |
|---|---|---|
| `vulnerability_results` | `pipeline_result["agent2_output"]["vulnerability_results"]` | `list[VulnerabilityResult]` |
| `pricing_predictions` | `pipeline_result["agent3_output"]["pricing_predictions"]` | `list[PricingPrediction]` |
| `action_recommendations` | `pipeline_result["agent4_output"]["action_recommendations"]` | `list[ActionRecommendation]` |
| `structured_profiles` | `pipeline_result["agent1_output"]["structured_profiles"]` | `list[dict]` |

---

## Section 1 — Portfolio Heatmap

**Chart type:** `plotly.graph_objects.Table`
**Columns:** Rank | Company | Vulnerability Score | Risk Level | Confidence | Peer Percentile
**Data source:** `vulnerability_results` sorted by `peer_rank`
**Colour scheme (row fill):**
- `critical` or `high` → `#FFCCCC` (red)
- `medium` → `#FFF3CC` (amber)
- `low` → `#CCFFCC` (green)

Header row uses a dark grey (`#2C3E50`) with white text.

---

## Section 2 — Component Breakdown

**Chart type:** `plotly.subplots.make_subplots` grid of horizontal bar charts
**One subplot per company**, laid out in a 2-column grid (ceil(n/2) rows).
**X-axis:** `weighted_score` (0–1 range)
**Y-axis:** component name (5 fixed names: `pricing_pressure`, `segment_coverage`, `feature_depth`, `strategic_signals`, `business_model_pressure`)
**Bar colour:** single accent colour (`#3498DB`) — keeping MVP simple.
**Data source:** `result.component_breakdown` for each `VulnerabilityResult`

---

## Section 3 — Pricing Prediction Summary

**Chart type:** `plotly.graph_objects.Table`
**Columns:** Company | Change Probability | Timeline | Risk Level | Top Driver
**Top Driver:** key from `p.drivers` with the highest float value
**Data source:** `pricing_predictions` sorted by `change_probability` descending
**Colour scheme (row fill):** same risk-level mapping as Section 1 (using `p.risk_level`)

---

## Section 4 — Action Recommendations

**Chart type:** `plotly.graph_objects.Table`
**Columns:** Priority | Company | Action Title | Owner | Due Window | Rationale
**Data source:** `action_recommendations` sorted by priority order (P0→P3)
**Colour scheme (row fill):**
- `P0` → `#FF4C4C` (red)
- `P1` → `#FFA500` (orange)
- `P2` → `#FFD700` (yellow)
- `P3` → `#EEEEEE` (light grey)

---

## Cell Structure

```python
# %% [Dashboard] RivalRadar Interactive Dashboard

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

# Guard
if 'pipeline_result' not in dir():
    raise RuntimeError("Run the pipeline cell first (pipeline_result not found).")

# Extract data
vulnerability_results = pipeline_result["agent2_output"]["vulnerability_results"]
pricing_predictions   = pipeline_result["agent3_output"]["pricing_predictions"]
action_recommendations = pipeline_result["agent4_output"]["action_recommendations"]

# --- Section 1: Portfolio Heatmap ---
# ... build and show fig1

# --- Section 2: Component Breakdown ---
# ... build subplots grid and show fig2

# --- Section 3: Pricing Prediction Summary ---
# ... build and show fig3

# --- Section 4: Action Recommendations ---
# ... build and show fig4
```

Each section calls `fig.show()` independently so sections render sequentially in the notebook output.

---

## Out of Scope (MVP)

- Dropdown/filter widgets (ipywidgets)
- Export to HTML or PDF
- Real-time refresh
- Responsive layout tuning
- Drill-down modals
