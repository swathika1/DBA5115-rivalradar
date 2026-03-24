# RivalRadar Dashboard UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Groq API fix to the existing pipeline and a new interactive Plotly dashboard cell to `agentic_pipeline.ipynb` that exports to a standalone `rivalradar_dashboard.html`.

**Architecture:** Two independent changes — (1) update `.env.example` and Cell 2 of the notebook to route API calls to Groq via `OPENAI_BASE_URL`, and (2) append a single new notebook cell that reads `pipeline_result` and renders four Plotly figures inline and as a self-contained HTML file.

**Tech Stack:** Python 3.13, Jupyter notebook (`nbformat`), Plotly (`plotly.graph_objects`, `plotly.subplots`, `plotly.io`), existing `openai` SDK (Groq-compatible endpoint).

---

## File Map

| File | Change |
|---|---|
| `rivalradar/.env.example` | Set `OPENAI_BASE_URL` and `OPENAI_MODEL` for Groq |
| `rivalradar/agentic_pipeline.ipynb` | Cell 2: add `OPENAI_BASE_URL` read + pass to client; append new dashboard cell at end |

No new files created. No other cells touched.

---

## Task 1: Groq API Fix — `.env.example`

**Files:**
- Modify: `rivalradar/.env.example`

- [ ] **Step 1: Update `.env.example`**

Set `OPENAI_BASE_URL` to Groq's OpenAI-compatible endpoint and `OPENAI_MODEL` to a supported Groq model. Keep `OPENAI_API_KEY` header name unchanged.

The file should read (keep your existing Groq key value in `OPENAI_API_KEY`, do not change it):
```
OPENAI_API_KEY=<your_groq_api_key>

# Optional for compatible gateways
OPENAI_BASE_URL=https://api.groq.com/openai/v1

OPENAI_MODEL=llama-3.3-70b-versatile

# Optional Azure OpenAI settings (used when endpoint, key, and deployment are set)
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_API_VERSION=2024-10-21

DB_PATH=rivalradar.db
LOG_LEVEL=INFO
```

Only edit `OPENAI_BASE_URL` and `OPENAI_MODEL` lines — leave the `OPENAI_API_KEY` value as-is.

- [ ] **Step 2: Verify the file looks correct**

```bash
cat rivalradar/.env.example
```
Expected: `OPENAI_BASE_URL=https://api.groq.com/openai/v1` and `OPENAI_MODEL=llama-3.3-70b-versatile` are present.

- [ ] **Step 3: Commit**

```bash
git add rivalradar/.env.example
git commit -m "feat: point OPENAI_BASE_URL to Groq endpoint, set llama-3.3-70b-versatile model"
```

---

## Task 2: Groq API Fix — Cell 2 of Notebook

**Files:**
- Modify: `rivalradar/agentic_pipeline.ipynb` (Cell 2 source only)

Cell 2 currently loads `OPENAI_API_KEY` and creates the client with no `base_url`. We need to also read `OPENAI_BASE_URL` and pass it through.

- [ ] **Step 1: Edit Cell 2 source in the notebook JSON**

Using Python, patch the notebook in place. Run this script from the repo root:

```python
import json
from pathlib import Path

nb_path = Path("rivalradar/agentic_pipeline.ipynb")
nb = json.loads(nb_path.read_text())

cell2_src = "".join(nb["cells"][2]["source"])

# Insert OPENAI_BASE_URL read after OPENAI_API_KEY line
old = 'OPENAI_API_KEY = _env.get("OPENAI_API_KEY", "").strip()'
new = (
    'OPENAI_API_KEY = _env.get("OPENAI_API_KEY", "").strip()\n'
    'OPENAI_BASE_URL = _env.get("OPENAI_BASE_URL", "").strip() or None'
)
assert old in cell2_src, "Could not find OPENAI_API_KEY line"
cell2_src = cell2_src.replace(old, new, 1)

# Update get_openai_client to pass base_url
old2 = "def get_openai_client() -> OpenAI:\n    return OpenAI(api_key=OPENAI_API_KEY)"
new2 = "def get_openai_client() -> OpenAI:\n    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)"
assert old2 in cell2_src, "Could not find get_openai_client definition"
cell2_src = cell2_src.replace(old2, new2, 1)

nb["cells"][2]["source"] = cell2_src
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print("Done. Cell 2 patched.")
```

Run from `rivalradar/` directory:
```bash
cd rivalradar && python3 ../patch_cell2.py
```

Or inline in the shell:
```bash
python3 - <<'EOF'
import json
from pathlib import Path

nb_path = Path("rivalradar/agentic_pipeline.ipynb")
nb = json.loads(nb_path.read_text())
cell2_src = "".join(nb["cells"][2]["source"])

old = 'OPENAI_API_KEY = _env.get("OPENAI_API_KEY", "").strip()'
new = ('OPENAI_API_KEY = _env.get("OPENAI_API_KEY", "").strip()\n'
       'OPENAI_BASE_URL = _env.get("OPENAI_BASE_URL", "").strip() or None')
assert old in cell2_src
cell2_src = cell2_src.replace(old, new, 1)

old2 = "def get_openai_client() -> OpenAI:\n    return OpenAI(api_key=OPENAI_API_KEY)"
new2 = "def get_openai_client() -> OpenAI:\n    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)"
assert old2 in cell2_src
cell2_src = cell2_src.replace(old2, new2, 1)

nb["cells"][2]["source"] = cell2_src
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print("Done.")
EOF
```

- [ ] **Step 2: Verify the patch**

```bash
python3 -c "
import json
nb = json.load(open('rivalradar/agentic_pipeline.ipynb'))
src = ''.join(nb['cells'][2]['source'])
assert 'OPENAI_BASE_URL' in src
assert 'base_url=OPENAI_BASE_URL' in src
print('Cell 2 patch verified OK')
"
```
Expected: `Cell 2 patch verified OK`

- [ ] **Step 3: Commit**

```bash
git add rivalradar/agentic_pipeline.ipynb
git commit -m "feat: pass OPENAI_BASE_URL to OpenAI client in Cell 2 (Groq support)"
```

---

## Task 3: Dashboard Cell — Build and Append

**Files:**
- Modify: `rivalradar/agentic_pipeline.ipynb` (append new cell)

Append a single new code cell at the end of the notebook containing the full dashboard implementation. Use the `nbformat` library (stdlib-adjacent; included in any Jupyter install) to append safely.

- [ ] **Step 1: Write the dashboard cell source**

Run this Python script to append the dashboard cell:

```bash
python3 - <<'SCRIPT'
import json
from pathlib import Path

DASHBOARD_SOURCE = '''\
# ── RivalRadar Interactive Dashboard ─────────────────────────────────────────
import math
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

# Guard: ensure pipeline has been run
if "pipeline_result" not in globals():
    raise RuntimeError(
        "pipeline_result not found. Run the pipeline cell (Cell 14) first."
    )

# ── Extract data ──────────────────────────────────────────────────────────────
_vuln   = pipeline_result["agent2_output"]["vulnerability_results"]
_price  = pipeline_result["agent3_output"]["pricing_predictions"]
_action = pipeline_result["agent4_output"]["action_recommendations"]

# ── Shared helpers ────────────────────────────────────────────────────────────
_HEADER_FILL   = "#2C3E50"
_HEADER_FONT   = "white"
_RISK_COLOURS  = {"critical": "#FFCCCC", "high": "#FFCCCC",
                  "medium":   "#FFF3CC", "low":  "#CCFFCC"}
_PRIO_COLOURS  = {"P0": "#FF4C4C", "P1": "#FFA500",
                  "P2": "#FFD700", "P3": "#EEEEEE"}

def _risk_col(level: str) -> str:
    return _RISK_COLOURS.get(str(level).lower(), "#FFFFFF")

def _fmt_pct(v) -> str:
    return f"{v:.0%}" if v is not None else "N/A"

def _prio_col(p: str) -> str:
    return _PRIO_COLOURS.get(str(p).upper(), "#FFFFFF")

def _header(fill=_HEADER_FILL, font=_HEADER_FONT):
    return dict(fill_color=fill, font=dict(color=font, size=13), align="left")

# ── Section 1: Portfolio Heatmap ──────────────────────────────────────────────
_v_sorted = sorted(_vuln, key=lambda r: (r.peer_rank or 999))
_row_cols1 = [_risk_col(r.risk_level) for r in _v_sorted]

fig1 = go.Figure(data=[go.Table(
    header=dict(
        values=["<b>Rank</b>", "<b>Company</b>", "<b>Vuln Score</b>",
                "<b>Risk Level</b>", "<b>Confidence</b>", "<b>Peer Percentile</b>"],
        **_header()
    ),
    cells=dict(
        values=[
            [r.peer_rank for r in _v_sorted],
            [r.company for r in _v_sorted],
            [f"{r.vulnerability_score:.3f}" for r in _v_sorted],
            [r.risk_level.upper() for r in _v_sorted],
            [f"{r.confidence:.0%}" for r in _v_sorted],
            [_fmt_pct(r.peer_percentile) for r in _v_sorted],
        ],
        fill_color=[_row_cols1] * 6,
        align="left",
        font=dict(size=12),
    )
)])
fig1.update_layout(title="<b>Section 1 — Portfolio Vulnerability Heatmap</b>",
                   margin=dict(l=20, r=20, t=50, b=10))
fig1.show()

# ── Section 2: Component Breakdown ───────────────────────────────────────────
_n      = len(_v_sorted)
_cols2  = 2
_rows2  = math.ceil(_n / _cols2)
_height2 = max(400, 300 * _rows2)

_COMP_NAMES = [
    "pricing_pressure", "segment_coverage", "feature_depth",
    "strategic_signals", "business_model_pressure"
]

fig2 = make_subplots(
    rows=_rows2, cols=_cols2,
    subplot_titles=[r.company for r in _v_sorted],
    shared_xaxes=False,
)

for idx, result in enumerate(_v_sorted):
    row = idx // _cols2 + 1
    col = idx % _cols2 + 1
    comp_map = {c.name: c.weighted_score for c in result.component_breakdown}
    scores = [comp_map.get(name, 0.0) for name in _COMP_NAMES]
    fig2.add_trace(
        go.Bar(
            x=scores,
            y=_COMP_NAMES,
            orientation="h",
            marker_color="#3498DB",
            showlegend=False,
            name=result.company,
        ),
        row=row, col=col
    )
    fig2.update_xaxes(range=[0, 1], row=row, col=col)

fig2.update_layout(
    title="<b>Section 2 — Component Breakdown (Weighted Scores)</b>",
    height=_height2,
    margin=dict(l=20, r=20, t=80, b=10),
)
fig2.show()

# ── Section 3: Pricing Prediction Summary ────────────────────────────────────
_p_sorted  = sorted(_price, key=lambda p: p.change_probability, reverse=True)
_row_cols3 = [_risk_col(p.risk_level) for p in _p_sorted]

def _top_driver(p) -> str:
    return max(p.drivers, key=p.drivers.get) if p.drivers else "N/A"

fig3 = go.Figure(data=[go.Table(
    header=dict(
        values=["<b>Company</b>", "<b>Change Probability</b>",
                "<b>Predicted Timeline</b>", "<b>Risk Level</b>", "<b>Top Driver</b>"],
        **_header()
    ),
    cells=dict(
        values=[
            [p.company for p in _p_sorted],
            [f"{p.change_probability:.0%}" for p in _p_sorted],
            [p.predicted_timeline for p in _p_sorted],
            [p.risk_level.upper() for p in _p_sorted],
            [_top_driver(p) for p in _p_sorted],
        ],
        fill_color=[_row_cols3] * 5,
        align="left",
        font=dict(size=12),
    )
)])
fig3.update_layout(title="<b>Section 3 — Pricing Prediction Summary</b>",
                   margin=dict(l=20, r=20, t=50, b=10))
fig3.show()

# ── Section 4: Action Recommendations ────────────────────────────────────────
_a_sorted  = sorted(
    _action,
    key=lambda a: int(a.priority[1]) if len(a.priority) >= 2 and a.priority[1].isdigit() else 99
)
_row_cols4 = [_prio_col(a.priority) for a in _a_sorted]

fig4 = go.Figure(data=[go.Table(
    header=dict(
        values=["<b>Priority</b>", "<b>Company</b>", "<b>Action Title</b>",
                "<b>Owner</b>", "<b>Due Window</b>", "<b>Rationale</b>"],
        **_header()
    ),
    cells=dict(
        values=[
            [a.priority for a in _a_sorted],
            [a.company for a in _a_sorted],
            [a.action_title for a in _a_sorted],
            [a.owner for a in _a_sorted],
            [a.due_window for a in _a_sorted],
            [a.rationale for a in _a_sorted],
        ],
        fill_color=[_row_cols4] * 6,
        align="left",
        font=dict(size=12),
    )
)])
fig4.update_layout(title="<b>Section 4 — Action Recommendations (P0 → P3)</b>",
                   margin=dict(l=20, r=20, t=50, b=10))
fig4.show()

# ── Export combined HTML ──────────────────────────────────────────────────────
# Path.cwd() in Jupyter resolves to the directory from which Jupyter was launched,
# which is typically the notebook directory.
_html_path = Path.cwd() / "rivalradar_dashboard.html"

_html_parts = [
    pio.to_html(fig1, full_html=False, include_plotlyjs="cdn"),
    pio.to_html(fig2, full_html=False, include_plotlyjs=False),
    pio.to_html(fig3, full_html=False, include_plotlyjs=False),
    pio.to_html(fig4, full_html=False, include_plotlyjs=False),
]
_full_html = (
    "<html><head><meta charset='utf-8'>"
    "<title>RivalRadar Dashboard</title></head>"
    "<body>" + "".join(_html_parts) + "</body></html>"
)
_html_path.write_text(_full_html, encoding="utf-8")
print(f"✓ Dashboard exported to: {_html_path.resolve()}")
'''

nb_path = Path("rivalradar/agentic_pipeline.ipynb")
nb = json.loads(nb_path.read_text())

new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": DASHBOARD_SOURCE,
}
nb["cells"].append(new_cell)
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print(f"Done. Notebook now has {len(nb['cells'])} cells.")
SCRIPT
```

- [ ] **Step 2: Verify the cell was appended**

```bash
python3 -c "
import json
nb = json.load(open('rivalradar/agentic_pipeline.ipynb'))
last = nb['cells'][-1]
assert last['cell_type'] == 'code'
assert 'rivalradar_dashboard.html' in ''.join(last['source'])
assert 'Section 1' in ''.join(last['source'])
assert 'Section 4' in ''.join(last['source'])
print(f'OK — notebook has {len(nb[\"cells\"])} cells, dashboard cell verified.')
"
```
Expected output contains: `OK — notebook has` followed by a cell count, and `dashboard cell verified.`

- [ ] **Step 3: Commit**

```bash
git add rivalradar/agentic_pipeline.ipynb
git commit -m "feat: add interactive Plotly dashboard cell with HTML export"
```

---

## Task 4: Smoke-Test the Dashboard

- [ ] **Step 1: Open the notebook in Jupyter and run all cells in order**

```bash
cd rivalradar && jupyter notebook agentic_pipeline.ipynb
```

Run cells top to bottom. Cell 14 must complete successfully (pipeline runs) before the dashboard cell can execute.

If Plotly is not installed:
```bash
pip install plotly
```

- [ ] **Step 2: Verify inline rendering**

After running the dashboard cell, confirm in the notebook output:
- Section 1 table renders with coloured rows (red/amber/green)
- Section 2 shows one horizontal bar chart per company in a grid
- Section 3 table renders with coloured rows
- Section 4 table renders with P0/P1/P2/P3 colour coding

- [ ] **Step 3: Verify HTML export**

```bash
ls -lh rivalradar/rivalradar_dashboard.html
open rivalradar/rivalradar_dashboard.html   # macOS
```

Confirm the file opens in the browser and all four sections are visible and interactive (hover tooltips work).

- [ ] **Step 4: Commit if any fixes were needed**

If you needed to tweak anything during smoke-test, commit the final state:
```bash
git add rivalradar/agentic_pipeline.ipynb
git commit -m "fix: dashboard smoke-test corrections"
```

---

## Done

After Task 4 passes, the deliverables are:

1. Pipeline routes to Groq via `OPENAI_BASE_URL` in `.env.example` and Cell 2
2. Dashboard cell (Cell 19) renders 4 interactive Plotly sections inline in Jupyter
3. `rivalradar/rivalradar_dashboard.html` — opens in any browser, no server needed
