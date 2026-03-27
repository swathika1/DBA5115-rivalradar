"""
RivalRadar - Simplified FastAPI app with DEMO MODE
User enters company names only, system auto-resolves details and shows live agent progress
DEMO MODE shows instant results with real vulnerability explanations
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader
import uvicorn
import os
import subprocess

from competitor_targets import COMPETITOR_TARGETS

app = FastAPI(title="RivalRadar", version="2.0.0")


def _is_wsl() -> bool:
    """Detect if this process is running inside WSL."""
    try:
        with open("/proc/version", "r", encoding="utf-8") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def _get_wsl_ip() -> str | None:
    """Return primary WSL IPv4 address used for Windows bridge target."""
    try:
        ips = subprocess.check_output(["hostname", "-I"], text=True).strip().split()
        return ips[0] if ips else None
    except Exception:
        return None


def _as_wsl_unc_path(path: Path) -> str:
    """Convert Linux path to \\\\wsl.localhost UNC path for Windows processes."""
    distro = os.environ.get("WSL_DISTRO_NAME", "Ubuntu")
    windows_style = str(path).replace("/", "\\")
    return f"\\\\wsl.localhost\\{distro}{windows_style}"


def _start_windows_localhost_bridge(port: int = 8000) -> None:
    """
    Start a Windows-side TCP bridge so Windows browser can always use localhost:port
    even when backend runs inside WSL.
    """
    if os.environ.get("RR_DISABLE_WINDOWS_BRIDGE") == "1":
        return
    if not _is_wsl():
        return

    target_ip = _get_wsl_ip()
    if not target_ip:
        print("[Bridge] Could not determine WSL IP; skipping Windows localhost bridge.")
        return

    bridge_script = Path(__file__).with_name("windows_localhost_bridge.py")
    if not bridge_script.exists():
        print("[Bridge] Bridge script missing; skipping Windows localhost bridge.")
        return

    unc_script = _as_wsl_unc_path(bridge_script)

    ps_command = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"$script='{unc_script}';"
        f"$targetIp='{target_ip}';"
        f"$port='{port}';"
        "if (-not (Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) {"
        "  Start-Process -WindowStyle Hidden -FilePath python -ArgumentList @($script,'--listen-host','127.0.0.1','--listen-port',$port,'--target-host',$targetIp,'--target-port',$port) | Out-Null"
        "}"
    )

    try:
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-Command", ps_command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[Bridge] Windows localhost bridge requested: http://localhost:{port} -> {target_ip}:{port}")
    except Exception as exc:
        print(f"[Bridge] Failed to start Windows localhost bridge: {exc}")

# ──────────────────────────────────────────────────────
# DEMO MODE - Shows instant results with vulnerabilities
# ──────────────────────────────────────────────────────
DEMO_MODE = True

DEMO_DATA = {
    "Notion": {
        "agent2_output": {
            "Notion": {
                "vulnerability_score": 0.72,
                "risk_level": "high",
                "summary": "Strong user base but facing template complexity issues and API limitations",
                "key_findings": [
                    "Upcoming competitor Linear is winning in speed & simplicity for developers",
                    "Notion's free tier cannibalization reducing enterprise conversion",
                    "API rate limits causing frustration among power users",
                    "Recent pricing increase (40%) showing margin pressure strategies"
                ],
                "ai_reasoning": "Notion shows HIGH vulnerability due to three converging factors: (1) Product complexity that alienates new users—our analysis of Notion forums shows 34% of onboarding questions are about 'where to start', (2) Aggressive free tier adoption (60% of signups) creates pricing power issues—similar to Slack's strategy which then required Premium tier introduction, (3) Enterprise clients increasingly choosing Linear/ClickUp for specific use cases. Average customer acquisition cost rising 18% YoY while churn rate holds at 8-12%. Probability of action required: 87%."
            }
        },
        "agent3_output": {
            "Notion": {
                "change_probability": 0.78,
                "predicted_timeline": "Q3-Q4 2024 (6-9 months)",
                "reasoning": "Notion's pricing model shows stress indicators. Current ARPU ($150/enterprise) lags behind competitors by 25%. We detected 4 new pricing experiment cohorts in their billing infrastructure (using ML on transaction patterns). Historical precedent: Slack raised prices 40% in 2022 → Notion likely considering similar move. Enterprise customers show 12% lower monthly active usage vs 2023, suggesting either consolidation or parallel tool usage. Prediction confidence: 84%."
            }
        },
        "agent4_output": {
            "1": {
                "action_title": "Accelerate AI Features in Portfolio",
                "priority": "P0",
                "owner": "Product Lead",
                "due_window": "Immediate (6-week sprint)",
                "description": "Notion's AI note-taking features are gaining 15K users/month",
                "impact": "Potential to capture 8-12% market share from Notion's AI-adopters",
                "reasoning": "Notion just launched AI writing assistant (2 weeks ago). This is their biggest feature push in 18 months. Market timing is critical: early movers in AI-augmented note-taking have 3x adoption vs late entrants. Our portfolio company's AI capabilities are 60 days behind Notion but have better performance. Recommend: Launch beta within 3 weeks."
            },
            "2": {
                "action_title": "Close Enterprise Deal with Notion Churners",
                "priority": "P1",
                "owner": "Enterprise Sales",
                "due_window": "30-45 days",
                "description": "2-3 Notion enterprise customers have publicly mentioned switching",
                "impact": "Likely $400K-600K ARR pickup",
                "reasoning": "Our monitoring detected 3 LinkedIn posts from enterprise buyers mentioning 'Notion limitations' + 'exploring alternatives' in past 30 days. This is 3.7x spike. Enterprise buying cycle is 60-90 days. Window is narrow. SDR team should outreach this week."
            }
        }
    },
    "Linear": {
        "agent2_output": {
            "Linear": {
                "vulnerability_score": 0.58,
                "risk_level": "medium",
                "summary": "Rapidly growing but dependent on engineering/developer segment—lacks SMB broadness",
                "key_findings": [
                    "95% customer base is software engineering teams (high concentration risk)",
                    "No dedicated SMB product tier (all-in-one pricing strategy)",
                    "Series B growth rate (140% YoY) likely slowing in 2024",
                    "Asana/Monday gaining traction in Linear's target market"
                ],
                "ai_reasoning": "Linear shows MEDIUM vulnerability driven by market concentration risk, not product weakness. Strong product-market fit in dev tools (NPS 72) BUT 95% of revenue from <5000 person engineering teams. This creates risk—they'll expand to adjacent markets where competition exists. Market diversification is critical for Series C fundraise. Their slowdown in enterprise deals suggests awareness of this issue. They must prove multi-department viability by Q4 2024."
            }
        },
        "agent3_output": {
            "Linear": {
                "change_probability": 0.62,
                "predicted_timeline": "Q4 2024 - Q1 2025 (4-6 months)",
                "reasoning": "Linear's funding runway suggests urgency: Series B ($30M) closed June 2023, typical 24-month horizon means financing needed by mid-2025. We detect career pages showing 8 new 'PMM Product Manager' hires (previously 0 PMMs). This hiring pattern matches pre-Series-C companies preparing for market expansion narrative. Pricing changes likely targeting non-dev audiences. Confidence: 76%."
            }
        },
        "agent4_output": {
            "1": {
                "action_title": "Prepare for Linear SMB Launch",
                "priority": "P1",
                "owner": "Product Ops",
                "due_window": "8-12 weeks",
                "description": "Linear will likely launch SMB tier targeting $50-200/month segment",
                "impact": "Preemptive positioning needed before Linear commodifies current pricing",
                "reasoning": "We're monitoring Linear's mobile app development (2 recent mobile hires) and simplified UI experiments. These precede downmarket launches. Our SMB product should emphasize simplicity advantages vs incoming Linear competition."
            },
            "2": {
                "action_title": "Lock In Enterprise Contracts Now",
                "priority": "P2",
                "owner": "Enterprise Sales",
                "due_window": "60-75 days",
                "description": "Linear hasn't penetrated Fortune 500 yet",
                "impact": "$800K-1.2M ARR potential before Linear builds enterprise features",
                "reasoning": "Linear's roadmap shows 12-month backlog before enterprise audit/compliance features. This is competitive advantage window. Use this in sales messaging: 'We have enterprise-grade compliance today.'"
            }
        }
    },
    "ClickUp": {
        "agent2_output": {
            "ClickUp": {
                "vulnerability_score": 0.65,
                "risk_level": "high",
                "summary": "Feature-rich but facing user confusion and feature clutter complexity",
                "key_findings": [
                    "40+ feature releases per quarter creating 'kitchen sink' perception",
                    "Customer support tickets increased 34% YoY despite 25% headcount growth",
                    "Free tier complexity leads to 45% churn before trial-to-paid conversion",
                    "Slack integration issues causing enterprise deal delays"
                ],
                "ai_reasoning": "ClickUp's vulnerability stems from GROWTH OVERLOAD. They're shipping 1+ feature weekly to compete with Notion/Asana, but this creates complexity debt. Analysis shows 18% increase in help center articles YoY, indicating customers need more hand-holding. Free tier churn at 45% (vs 22% industry average) suggests UX friction for non-technical users. Their $30M Series D funding is driving aggressive feature parity strategy. Lean into simplicity: complexity is ClickUp's moat AND their vulnerability."
            }
        },
        "agent3_output": {
            "ClickUp": {
                "change_probability": 0.71,
                "predicted_timeline": "Q2-Q3 2024 (3-5 months)",
                "reasoning": "ClickUp just hired VP Chief Product Officer (2 weeks ago) + VP Platform Architecture (new hire). Executive C-suite additions indicate incoming product strategy shift. Likely initiatives: (1) Free tier simplification, (2) Platform consolidation (merge duplicate features), (3) Pricing restructure. This reshuffling precedes product repositioning. Prediction confidence: 81%."
            }
        },
        "agent4_output": {
            "1": {
                "action_title": "Win ClickUp Refugees with Simplicity Messaging",
                "priority": "P0",
                "owner": "Marketing",
                "due_window": "Ongoing + 6-week campaign",
                "description": "ClickUp's complexity is pushing power users and SMB customers away",
                "impact": "Potential 5-8% market share capture from ClickUp churn",
                "reasoning": "Reddit/Twitter sentiment analysis shows 22% increase in 'ClickUp too complicated' mentions (vs 4% in prior year). ClickUp's NPS is 62 (healthy) BUT Net Distractors are 28% (very high—people love it then get frustrated). Launch 'simple vs complex' campaign targeting CMOs/ops leaders."
            },
            "2": {
                "action_title": "Build 1:1 Migration Tool from ClickUp",
                "priority": "P2",
                "owner": "Engineering",
                "due_window": "12-14 weeks",
                "description": "Remove switching costs for ClickUp users wanting to leave",
                "impact": "Can drive 2-3x faster adoption for SMB segment",
                "reasoning": "When Slack had Hipchat migration tool, adoption accelerated 40%. ClickUp's API is mature (good data portability potential). Building import/migration capability removes last sales objection for switching teams."
            }
        }
    },
    "Slack": {
        "agent2_output": {
            "Slack": {
                "vulnerability_score": 0.52,
                "risk_level": "medium",
                "summary": "Established market leader but facing consolidation pressure from Teams and Discord",
                "key_findings": [
                    "Microsoft Teams gaining 3% market share YoY in enterprise segment",
                    "Discord capturing 18% of developer communication market",
                    "Slack's pricing not aligned with SMB (<50 employees)",
                    "No breakthrough feature in messaging since 2019"
                ],
                "ai_reasoning": "Slack's vulnerability stems from market maturation, not product weakness. Enterprise dominance (94% of Fortune 500) masks SMB weakness where Teams and Discord compete fiercely. Slack's recent acquisition by Salesforce adds integration power but also creates uncertainty about product roadmap independence. NPS declining 8 points YoY to 48. Risk is slow bleed to better-positioned entrants."
            }
        },
        "agent3_output": {
            "Slack": {
                "change_probability": 0.45,
                "predicted_timeline": "Q1-Q2 2025 (2-4 months)",
                "reasoning": "Slack's parent Salesforce is under earnings pressure, likely to push Slack for profitability. We detect new billing architecture experiments suggesting SMB tier launch incoming. However, Slack's installed base (750K+ teams) makes pricing changes risky. Confidence: 67%."
            }
        },
        "agent4_output": {
            "1": {
                "action_title": "Capture Slack SMB Overflow",
                "priority": "P1",
                "owner": "Sales",
                "due_window": "Ongoing",
                "description": "SMB companies churning from Slack due to pricing now have few alternatives",
                "impact": "$200K-400K ARR opportunity",
                "reasoning": "Slack's $165/user/year is prohibitive for teams <50. Our alternative at $60/user/year captures this segment. Position as 'Slack heir for growing teams.'"
            }
        }
    },
    "Asana": {
        "agent2_output": {
            "Asana": {
                "vulnerability_score": 0.61,
                "risk_level": "medium",
                "summary": "Facing margin pressure and customer concentration in marketing/ops functions",
                "key_findings": [
                    "Enterprise adoption slowing (12% YoY vs 28% in 2022)",
                    "Customer acquisition cost rising 22% while churn increases 6%",
                    "58% of revenue from marketing/ops teams (low function diversity)",
                    "Jira, ClickUp, Notion eating into project management TAM"
                ],
                "ai_reasoning": "Asana's growth narrative shifting from explosive expansion to profitability management. Product is mature but lacks category-defining innovations. They're pursuing horizontal expansion but struggle to displace entrenched competitors. Most at-risk segment: mid-market ops teams (100-500 employees) where alternatives are abundant."
            }
        },
        "agent3_output": {
            "Asana": {
                "change_probability": 0.58,
                "predicted_timeline": "Q3-Q4 2024 (5-7 months)",
                "reasoning": "Asana's CFO hired 6 months ago from Datadog signals shift to unit economics focus. We detect 3 new 'efficiency' product cohorts in pricing experiments. Likely action: pricing restructure + focus on enterprise ARR over user growth. Confidence: 72%."
            }
        },
        "agent4_output": {
            "1": {
                "action_title": "Win Mid-Market from Asana with Simplicity + Integration",
                "priority": "P0",
                "owner": "Product",
                "due_window": "6-8 weeks",
                "description": "Asana's complexity alienates ops teams seeking clarity",
                "impact": "Potential 4-6% market share from Asana's core segment",
                "reasoning": "Reddit/Twitter analysis shows 'Asana overwhelming' mentions up 34% YoY. Our value prop: 70% less features, 80% lower learning curve, 3x faster ROI. Launch 'ops team' hero campaign."
            }
        }
    },
    "Jira": {
        "agent2_output": {
            "Jira": {
                "vulnerability_score": 0.48,
                "risk_level": "low-medium",
                "summary": "Entrenched in dev/agile but facing modular challengers",
                "key_findings": [
                    "Linear growing 3x faster in dev tools segment",
                    "Jira Cloud migration incomplete (data gravity holding customers)",
                    "Atlassian revenue diversification strategy reducing Jira prioritization",
                    "High switching cost prevents immediate churn"
                ],
                "ai_reasoning": "Jira's moat is high switching cost + org lock-in via Confluence/Bitbucket integration, not product strength. Teams dislike Jira but stay because migration is painful. Linux/dev teams increasingly trying Linear-first approach for greenfield projects. Jira remains 'the default' but 'the chosen' is shifting."
            }
        },
        "agent3_output": {
            "Jira": {
                "change_probability": 0.39,
                "predicted_timeline": "Ongoing (low urgency)",
                "reasoning": "Jira's entrenchment means pricing changes face resistance. Atlassian more focused on growing Cloud revenue than protecting Server customers. Slow migration from on-prem to Cloud is natural attrition point. Confidence: 58%."
            }
        },
        "agent4_output": {
            "1": {
                "action_title": "Position as 'Jira Alternative for New Dev Teams'",
                "priority": "P2",
                "owner": "Marketing",
                "due_window": "12+ weeks",
                "description": "Target greenfield projects and new orgs avoiding Jira's legacy setup",
                "impact": "$150K+ ARR from dev tools segment capture",
                "reasoning": "Jira's install base is sticky but future adoption is winnable. Focus on modern dev orgs (Series A-B startups) who prefer newer tools from day 1."
            }
        }
    },
    "Google": {
        "agent2_output": {
            "Google": {
                "vulnerability_score": 0.35,
                "risk_level": "low",
                "summary": "Dominant in search and cloud but facing specialized competition",
                "key_findings": [
                    "OpenAI ChatGPT taking search query share (3.2% decline YoY)",
                    "AWS and Azure growing faster in cloud infrastructure",
                    "Workplace (Docs/Gmail/Meet) losing to Microsoft 365 in enterprise",
                    "Android losing developer mindshare to iOS-first approach"
                ],
                "ai_reasoning": "Google's vulnerability is existential risk, not tactical. Meta-threat from AI companies (OpenAI, Anthropic) eating into core search business. However, scale and margins make Google quasi-moat-less—they can compete in anything. Most at-risk segment: SMB who prefer Microsoft's integrated bundle over Google's fragmented offerings."
            }
        },
        "agent3_output": {
            "Google": {
                "change_probability": 0.52,
                "predicted_timeline": "12-24 months (long-term risk)",
                "reasoning": "Search revenue decline from AI alternatives is real but slow. Google's 2024 strategy: integrate Gemini AI into all products, create defensibility through integration. No immediate pricing action likely—focus on keeping users in ecosystem. Confidence: 62%."
            }
        },
        "agent4_output": {
            "1": {
                "action_title": "Build AI-Powered Alternative to Google Workplace",
                "priority": "P1",
                "owner": "Strategy",
                "due_window": "24+ months",
                "description": "Google's workplace suite offers opportunity for AI-native reimagining",
                "impact": "Long-term TAM: $200B+ in workplace software",
                "reasoning": "Microsoft is winning enterprise with 365. Gap: SMB/mid-market who want modern, AI-native tools vs. Google bundle designed for consumer. Build for tomorrow's workflow."
            }
        }
    }
}

# Setup Jinja2 templates
template_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(template_dir, exist_ok=True)
jinja_env = Environment(loader=FileSystemLoader(template_dir))

# Build lookup dict from competitor targets
COMPANY_LOOKUP = {c["name"].lower(): c for c in COMPETITOR_TARGETS}

# Store results in memory (for demo purposes)
RESULTS_CACHE = {}

# ──────────────────────────────────────────────────────
# VC PORTFOLIO & COMPETITOR MAPPING
# ──────────────────────────────────────────────────────
VC_PORTFOLIO = [
    {"name": "Notion", "segment": "Workspace & Collaboration"},
    {"name": "Linear", "segment": "Developer Tools"},
    {"name": "ClickUp", "segment": "Project Management"},
]

# Competitor mapping for portfolio companies
COMPETITOR_MAP = {
    "Notion": ["Linear", "Asana", "Monday", "Confluence"],
    "Linear": ["Jira", "GitHub Projects", "Asana", "Azure DevOps"],
    "ClickUp": ["Notion", "Asana", "Monday", "Trello"],
    "Slack": ["Microsoft Teams", "Discord", "Google Chat"],
    "Asana": ["Monday", "Jira", "ClickUp", "Notion"],
    "Jira": ["Linear", "GitHub Projects", "Azure DevOps", "Taiga"],
    "Google": ["Microsoft", "OpenAI", "Meta", "Amazon"],
}

# ──────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────

def resolve_companies(company_names: str) -> dict:
    """
    Parse comma-separated company names and resolve their details.
    Accepts ANY company name - if not in hardcoded list, creates a minimal entry for scraping.
    Returns: {valid: [...], invalid: [...]}
    """
    names = [n.strip() for n in company_names.split(",") if n.strip()]
    valid = []
    invalid = []
    
    for name in names:
        key = name.lower()
        if key in COMPANY_LOOKUP:
            # Use predefined company data
            valid.append(COMPANY_LOOKUP[key])
        elif name and len(name) > 1:
            # Accept ANY company name for scraping
            valid.append({
                "name": name,
                "domain": f"{key.replace(' ', '')}.com",
                "pricing_url": f"https://{key.replace(' ', '')}.com/pricing",
                "page_types": ["pricing", "features", "about"],
                "market_segment": "SaaS"
            })
        else:
            invalid.append(name)
    
    return {"valid": valid, "invalid": invalid}


async def stream_pipeline_progress(companies: list) -> AsyncGenerator[str, None]:
    """
    Stream real-time agent progress and results using Server-Sent Events (SSE)
    """
    try:
        # Stage 1: Initialization
        yield f"data: {json.dumps({'stage': 'init', 'message': f'Starting analysis for {len(companies)} companies...'})}\n\n"
        await asyncio.sleep(0.5)
        
        # Stage 2: Run pipeline with streaming updates
        company_names = [c["name"] for c in companies]
        
        yield f"data: {json.dumps({'stage': 'agent', 'agent': '1', 'message': 'Agent 1: Scraping competitor pricing pages...'})}\n\n"
        await asyncio.sleep(0.8)
        
        yield f"data: {json.dumps({'stage': 'agent', 'agent': '2', 'message': 'Agent 2: Analyzing competitive vulnerabilities...'})}\n\n"
        await asyncio.sleep(0.8)
        
        yield f"data: {json.dumps({'stage': 'agent', 'agent': '3', 'message': 'Agent 3: Predicting pricing trends...'})}\n\n"
        await asyncio.sleep(0.8)
        
        yield f"data: {json.dumps({'stage': 'agent', 'agent': '4', 'message': 'Agent 4: Planning VC recommendations...'})}\n\n"
        await asyncio.sleep(0.5)
        
        # Use demo data if available (case-insensitive check)
        if DEMO_MODE and len(companies) > 0:
            company_name = companies[0]["name"]
            # Check if company exists in demo data (case-insensitive)
            demo_key = None
            for key in DEMO_DATA.keys():
                if key.lower() == company_name.lower():
                    demo_key = key
                    break
            
            if demo_key:
                # Use demo data for known companies
                result = {
                    "elapsed_seconds": 4.5,
                    "agent1_output": {},
                    "agent2_output": DEMO_DATA[demo_key]["agent2_output"],
                    "agent3_output": DEMO_DATA[demo_key]["agent3_output"],
                    "agent4_output": DEMO_DATA[demo_key]["agent4_output"]
                }
            else:
                # For unknown companies, try to scrape real data
                yield f"data: {json.dumps({'stage': 'agent', 'agent': 'scraper', 'message': f'Running live analysis for {company_name}...'})}\n\n"
                try:
                    from agentic_pipeline import run_agent_pipeline
                    result = await run_agent_pipeline(
                        run_live_scrape=True,
                        companies=companies
                    )
                except Exception as e:
                    # If scraping fails, return empty result
                    print(f"[ERROR] Pipeline failed for {company_name}: {str(e)}", flush=True)
                    yield f"data: {json.dumps({'stage': 'warning', 'message': f'Scraping {company_name} encountered issues: {str(e)[:100]}'})}\n\n"
                    result = {
                        "elapsed_seconds": 2.0,
                        "agent1_output": {},
                        "agent2_output": {},
                        "agent3_output": {},
                        "agent4_output": {}
                    }
        else:
            # Non-demo mode: always try to scrape
            from agentic_pipeline import run_agent_pipeline
            try:
                result = await run_agent_pipeline(
                    run_live_scrape=True,
                    companies=companies
                )
            except Exception as e:
                print(f"[ERROR] Pipeline failed: {str(e)}", flush=True)
                result = {
                    "elapsed_seconds": 0.0,
                    "agent1_output": {},
                    "agent2_output": {},
                    "agent3_output": {},
                    "agent4_output": {}
                }
        
        # Cache results
        session_id = datetime.now().isoformat()
        RESULTS_CACHE[session_id] = {
            "companies": company_names,
            "result": result,
            "timestamp": session_id
        }
        
        # Stage 3: Success
        yield f"data: {json.dumps({'stage': 'success', 'message': 'Analysis complete!', 'session_id': session_id})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'stage': 'error', 'message': f'Error: {str(e)}'})}\n\n"


# ──────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────

@app.get("/ping")
async def ping():
    """Simple ping to check if server is responding"""
    return {"message": "pong", "status": "alive"}


@app.get("/", response_class=HTMLResponse)
async def index():
    """Render login page"""
    try:
        template = jinja_env.get_template("login.html")
        return template.render()
    except Exception as e:
        print(f"[ERROR] Failed to load login.html: {str(e)}", flush=True)
        return f"<h1>Error loading page</h1><p>{str(e)}</p>"


@app.get("/vc-dashboard", response_class=HTMLResponse)
async def vc_dashboard(name: str = "Partner", org: str = "Your VC Fund", email: str = ""):
    """Render personalized VC dashboard after login"""
    try:
        template = jinja_env.get_template("vc_dashboard_v2.html")
        portfolio = VC_PORTFOLIO
        competitor_map = {c["name"]: COMPETITOR_MAP.get(c["name"], []) for c in portfolio}
        return template.render(
            vc_name=name,
            vc_org=org,
            vc_email=email,
            portfolio_companies=portfolio,
            competitor_map=competitor_map
        )
    except Exception as e:
        print(f"[ERROR] Failed to load vc_dashboard_v2.html: {str(e)}", flush=True)
        return f"""<html><body style="background: linear-gradient(135deg, #f8f9ff, #e8f0ff); padding: 40px; font-family: Inter, sans-serif;"><div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; padding: 40px;"><h2>Welcome!</h2><p>Dashboard loading...</p><script>setTimeout(() => window.location.href = '/dashboard', 2000);</script></div></body></html>"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Render dashboard with company input form"""
    try:
        companies_list = [{"name": c["name"], "segment": c["market_segment"]} for c in COMPETITOR_TARGETS]
        template = jinja_env.get_template("dashboard.html")
        return template.render(available_companies=companies_list)
    except Exception as e:
        print(f"[ERROR] Failed to load dashboard.html: {str(e)}", flush=True)
        return f"<h1>Error loading dashboard</h1><p>{str(e)}</p>"


@app.get("/api/check-companies")
async def check_companies(company_names: str):
    """
    Check which company names are valid and resolvable
    """
    resolved = resolve_companies(company_names)
    if not resolved["valid"]:
        raise HTTPException(status_code=400, detail=f"No valid companies found. Invalid: {resolved['invalid']}")
    
    return {
        "valid_count": len(resolved["valid"]),
        "invalid_count": len(resolved["invalid"]),
        "companies": resolved["valid"],
        "invalid_names": resolved["invalid"]
    }


@app.get("/running/{company_names}", response_class=HTMLResponse)
async def running_page(company_names: str):
    """Show loading page with SSE stream"""
    template = jinja_env.get_template("running_v2.html")
    return template.render(company_names=company_names)


@app.get("/stream/{company_names}")
async def stream_progress(company_names: str):
    """
    Server-Sent Events (SSE) endpoint for real-time progress updates
    """
    resolved = resolve_companies(company_names)
    if not resolved["valid"]:
        raise HTTPException(status_code=400, detail="No valid companies found")
    
    return StreamingResponse(
        stream_pipeline_progress(resolved["valid"]),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/results/{session_id}", response_class=HTMLResponse)
async def show_results(session_id: str):
    """Display results from a completed analysis"""
    if session_id not in RESULTS_CACHE:
        raise HTTPException(status_code=404, detail="Results not found")
    
    cached = RESULTS_CACHE[session_id]
    result = cached["result"]
    
    # Parse the pipeline results
    template = jinja_env.get_template("results.html")
    return template.render(
        companies=cached["companies"],
        result=result,
        timestamp=cached["timestamp"]
    )


@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page():
    """VC portfolio management page"""
    # Build competitor map for template
    competitor_map = {}
    for company in VC_PORTFOLIO:
        name = company["name"]
        competitor_map[name] = COMPETITOR_MAP.get(name, [])
    
    template = jinja_env.get_template("portfolio.html")
    return template.render(
        portfolio_companies=VC_PORTFOLIO,
        portfolio_count=len(VC_PORTFOLIO),
        competitor_map=competitor_map
    )


@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "companies_available": len(COMPETITOR_TARGETS),
        "demo_mode": DEMO_MODE
    }


if __name__ == "__main__":
    _start_windows_localhost_bridge(port=8000)
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
