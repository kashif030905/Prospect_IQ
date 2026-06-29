# ProspectIQ — System Architecture

> **Version:** 2.0.0 · **Stack:** LangGraph · LLaMA 3.1 8B · Tavily · FastAPI · Streamlit · SQLite

---

## 1. Overview

![ProspectIQ Architecture](diagrams/architecture.png)

ProspectIQ is a multi-agent AI platform for automated B2B customer discovery. It accepts five user inputs and runs them through a sequential pipeline of 7 specialised AI agents, each with a distinct responsibility. All agents share a single typed state object — `ProspectIQState` — and communicate exclusively through it. No agent calls another directly.

The system is split into four layers:

| Layer | Technology | Port |
|-------|-----------|------|
| Agent Orchestration | LangGraph 0.4.8 | — |
| Backend API | FastAPI + Uvicorn | 8000 |
| Frontend UI | Streamlit | 8501 |
| Persistence | SQLite via SQLAlchemy | — |

---

## 2. High-Level Flow

```
User (Streamlit UI)
        │
        │  POST /api/analyze
        ▼
  FastAPI Backend
        │
        │  discovery_graph.invoke(initial_state)
        ▼
  LangGraph Pipeline
  ┌─────────────────────────────────────────────────────┐
  │  planner_node → icp_node → web_search_node          │
  │      → validation_node → decision_maker_node        │
  │          → enrichment_node → recommendation_node    │
  └─────────────────────────────────────────────────────┘
        │
        │  ProspectIQState (fully populated)
        ▼
  FastAPI saves session to SQLite → returns JSON to frontend
        │
        ▼
  Streamlit renders 6-tab dashboard
        │
        ├── Download PDF  →  POST /api/report  →  PyMuPDF
        └── Approve/Reject →  POST /api/approve  →  SQLite update
```

---

## 3. Shared State — `ProspectIQState`

Defined in `agents/state.py` as a Python `TypedDict`. Every agent receives the full state, reads what it needs, writes its output, and returns the updated state to LangGraph.

```
ProspectIQState
├── User Inputs (set once at pipeline start)
│   ├── product_description   str
│   ├── target_industry       str
│   ├── company_size          str
│   ├── target_persona        str
│   └── target_location       str   ← hard filter enforced by every agent
│
├── Agent Outputs (populated sequentially)
│   ├── plan                  Optional[str]   ← Planner Agent
│   ├── icp_profile           Optional[str]   ← ICP Agent
│   ├── companies_found       Optional[str]   ← Web Search Agent
│   ├── validated_companies   Optional[str]   ← Validation Agent
│   ├── decision_makers       Optional[str]   ← Decision Maker Agent
│   ├── enriched_contacts     Optional[str]   ← Enrichment Agent
│   └── recommendations       Optional[str]   ← Recommendation Agent
│
└── Control
    └── human_approved        Optional[bool]  ← set via /api/approve
```

---

## 4. Agent Pipeline

### Graph Definition (`agents/graph.py`)

```
START
  └─► planner_node
        └─► icp_node
              └─► web_search_node
                    └─► validation_node
                          └─► decision_maker_node
                                └─► enrichment_node
                                      └─► recommendation_node
                                              └─► END
```

The graph is compiled once at import time (`discovery_graph = create_discovery_graph()`) and reused for every request.

---

### Agent 1 — Planner Agent (`agents/planner_agent.py`)

**Reads:** `product_description`, `target_industry`, `company_size`, `target_persona`, `target_location`  
**Writes:** `plan`  
**Tools:** LLM only (no web search)

Generates a location-specific B2B discovery strategy covering market overview, ideal customer characteristics, search strategy, qualification criteria, decision maker approach, and outreach considerations. Sets the context for all downstream agents.

---

### Agent 2 — ICP Agent (`agents/icp_agent.py`)

**Reads:** all user inputs + `plan`  
**Writes:** `icp_profile`  
**Tools:** LLM only

Defines the Ideal Customer Profile with five sections: company profile, pain points, buying signals, qualification criteria (must-have / nice-to-have / disqualifiers), and location-specific search queries. Location is explicitly listed as a hard must-have and an automatic disqualifier if unmet.

---

### Agent 3 — Web Search Agent (`agents/web_search_agent.py`)

**Reads:** `target_industry`, `target_location`, `company_size`, `target_persona`, `icp_profile`  
**Writes:** `companies_found`  
**Tools:** LLM + Tavily (parallel)

**Search strategy:**
1. LLM generates 5 location-specific search queries
2. All 5 queries fire simultaneously via `ThreadPoolExecutor(max_workers=5)`
3. Results are deduplicated by URL
4. LLM extracts verified companies from the combined raw results

Only companies explicitly located in `target_location` are included. The extraction prompt enforces this with `CRITICAL RULES` — hallucinated or off-location companies are rejected.

---

### Agent 4 — Company Validation Agent (`agents/company_validation_agent.py`)

**Reads:** `product_description`, `target_location`, `icp_profile`, `companies_found`  
**Writes:** `validated_companies`  
**Tools:** LLM only

Scores each company out of 100 using a weighted rubric:

| Criterion | Points | Notes |
|-----------|--------|-------|
| Location match | 30 | Hard disqualifier — 0 if outside target location |
| Industry fit | 25 | |
| Company size match | 20 | |
| Pain point fit | 15 | |
| Growth signals | 10 | |

**Verdict thresholds:** 80–100 Strong Fit, 60–79 Medium Fit, 40–59 Weak Fit, 0–39 No Fit, 0 (disqualified).

Output includes per-company scoring cards, a comparison table, and a ranked shortlist of the top 3 companies.

---

### Agent 5 — Decision Maker Agent (`agents/decision_maker_agent.py`)

**Reads:** `validated_companies`, `target_location`, `target_persona`  
**Writes:** `decision_makers`  
**Tools:** LLM + Tavily (sequential, per company)

**Process:**
1. LLM extracts the top 3 company names from `validated_companies`
2. For each company: 3 parallel Tavily searches (LinkedIn, web, site-specific LinkedIn)
3. LLM synthesises results into a structured decision maker profile
4. Sequential processing with `time.sleep(2)` between companies to respect Groq rate limits
5. Final LLM call produces an outreach priority summary

Output includes name (or "To be verified"), title, seniority, confidence level, LinkedIn URL, and a rationale for why this person is the right contact.

---

### Agent 6 — Contact Enrichment Agent (`agents/contact_enrichment_agent.py`)

**Reads:** `decision_makers`, `target_location`, `target_industry`, `target_persona`  
**Writes:** `enriched_contacts`  
**Tools:** LLM + Tavily (parallel searches, sequential contacts)

**Process:**
1. LLM extracts up to 3 contacts from `decision_makers` in `Company | Name | Title` format
2. For each contact: 3 parallel Tavily searches (email, LinkedIn, company contact details)
3. LLM enriches each contact with email, LinkedIn, best channel, best time, hook, subject line, opening line, value prop, and CTA
4. Final LLM call produces an outreach strategy overview

Email addresses are marked `(Verified)` if found in search results or `(Inferred)` if derived from the company's email pattern.

---

### Agent 7 — Recommendation Agent (`agents/recommendation_agent.py`)

**Reads:** all state fields  
**Writes:** `recommendations`  
**Tools:** LLM only

Synthesises all prior agent outputs into an executive-level sales playbook. Uses regex-based parsing internally to extract company names and scores from `validated_companies` before prompting the LLM — this prevents the model from inventing placeholder companies or misquoting scores.

Output sections:
- Executive Summary
- Top Prospect — Immediate Action
- Prioritised Prospect List (table)
- 14-Day Outreach Sequence
- Email Templates (A for top prospect, B for others)
- Expected Outcomes table
- Immediate Next Steps
- Risks & Mitigation table

---

## 5. Backend (`backend/`)

### Entry Point — `backend/main.py`

```
FastAPI app
├── CORS middleware (allow_origins=["*"])
├── startup event → init_db()
├── GET  /               health check
└── router → /api        (backend/routes/discovery.py)
```

### API Routes — `backend/routes/discovery.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Runs the full LangGraph pipeline. Saves session to DB. Returns all 7 agent outputs. |
| `POST` | `/api/approve` | Sets approval status (`approved` / `rejected`). Updates DB if `session_id` provided. |
| `GET`  | `/api/sessions` | Returns all past sessions (id, timestamps, inputs, status) ordered by recency. |
| `GET`  | `/api/sessions/{session_id}` | Returns full output of a specific past session. |
| `POST` | `/api/report` | Generates and returns 8-page PDF. Accepts pre-computed results — never re-runs pipeline. |

**Input contract** (`DiscoveryRequest`):

```python
product_description:  str
target_industry:      str
target_company_size:  str        # remapped to company_size for state
target_role:          str        # remapped to target_persona for state
target_location:      str = "Not specified"
```

### Persistence — `backend/database.py`

SQLite database (`prospectiq.db`) managed via SQLAlchemy ORM.

```
DiscoverySession (table: sessions)
├── id                   UUID (primary key)
├── created_at           DateTime
├── product_description  Text
├── target_industry      String
├── company_size         String
├── target_persona       String
├── target_location      String
├── status               String  ("completed" / "approved" / "rejected")
└── [7 agent output columns: plan, icp_profile, companies_found,
    validated_companies, decision_makers, enriched_contacts, recommendations]
```

CRUD operations: `save_session()`, `get_all_sessions()`, `get_session_by_id()`, `update_session_status()`.

### PDF Generation — `backend/services/pdf_service.py`

Uses PyMuPDF (`fitz`) with low-level drawing primitives. Generates an 8-page report:

| Page | Content |
|------|---------|
| 1 | Cover (navy background, product/location/persona metadata) |
| 2 | Table of Contents + summary stat cards |
| 3 | Discovery Strategy & Plan |
| 4 | Ideal Customer Profile |
| 5 | Companies Found |
| 6 | Company Validation & Scores (with legend) |
| 7 | Decision Makers + Enriched Contacts |
| 8 | Final Recommendations + approval sign-off box |

The `generate_pdf_report(results, vendor_names)` function accepts pre-computed results passed from the frontend — it does not invoke any agents.

---

## 6. Frontend (`frontend/`)

### Entry Point — `frontend/app.py`

Streamlit application on port 8501.

**Layout:**
```
Page
├── Welcome Banner (animated, shows live prospect count)
├── Sidebar
│   ├── Past Sessions (loads from GET /api/sessions, up to 5 shown)
│   ├── Agent descriptions (expandable)
│   └── System info
├── Agent Pipeline tracker (7 status metrics)
├── Input Form  (upload_section.py)
├── Start Discovery button → POST /api/analyze
├── Results Dashboard (results_section.py)
├── PDF Download → POST /api/report (cached with st.cache_data)
└── Approval Section (approval_section.py)
```

### Components

**`frontend/components/upload_section.py`**  
Five-field input form. Uses a `reset_count` key pattern to force widget re-render on reset. Returns a dict only when all required fields (product, industry, location) are filled.

**`frontend/components/results_section.py`**  
6-tab dashboard. Parses raw LLM text from each agent using regex. Key functions:

| Function | Purpose |
|----------|---------|
| `count_prospects()` | Counts validated companies via regex for banner counter |
| `_extract_scores_map()` | Parses scores from validation text for recommendation display |
| `_render_companies()` | Parses `={30,}` delimiters into structured company cards |
| `_render_validated()` | Parses `COMPANY \d*:` blocks into scored cards with progress bars |
| `_render_decision_makers()` | Parses contact blocks into profile cards |
| `_render_enriched()` | Parses enrichment blocks into contact cards with email templates |
| `_render_recommendation()` | Parses `## ` sections into structured playbook components |

**`frontend/components/approval_section.py`**  
Two buttons — Approve and Reject — each calling `POST /api/approve`.

---

## 7. Configuration (`config/settings.py`)

All secrets loaded from `.env` via `python-dotenv`.

| Variable | Used by |
|----------|---------|
| `GROQ_API_KEY` | All 7 agents (LLM calls) |
| `TAVILY_API_KEY` | Web Search, Decision Maker, Enrichment agents |
| `GROQ_MODEL` | Defaults to `llama-3.1-8b-instant` |
| `ANTHROPIC_API_KEY` | Declared, reserved for future use |
| `GEMINI_API_KEY` | Declared, reserved for future use |

---

## 8. Key Design Decisions

### Location as a Hard Disqualifier
`target_location` is enforced at every stage of the pipeline. The ICP Agent lists it as a mandatory qualifier. The Web Search Agent includes it in every query and rejects results without it. The Validation Agent assigns 0/30 location points and marks companies as `DISQUALIFIED` if they are not in the target geography. This prevents the most common failure mode of AI sales tools — geographically irrelevant leads.

### Parallel Search, Sequential LLM Calls
Tavily searches within each agent run in parallel via `ThreadPoolExecutor`. LLM calls are sequential with `time.sleep(1–2)` delays between them. This maximises search throughput while staying within Groq's free-tier rate limits.

### Regex-Guarded Prompting in Recommendation Agent
Before building the final prompt, `recommendation_agent.py` uses regex to extract company names and scores from `validated_companies`. These verified values are injected directly into the prompt with explicit instructions not to deviate from them. This prevents the LLM from inventing placeholder companies or misquoting scores.

### State Key Contract
All 7 agent output keys (`plan`, `icp_profile`, `companies_found`, `validated_companies`, `decision_makers`, `enriched_contacts`, `recommendations`) are identical across the LangGraph state, the FastAPI response, the SQLite schema, and the Streamlit renderer. Any mismatch breaks the pipeline — the keys are locked in `state.py` and never aliased.

### No Pipeline Re-runs on PDF/Reload
The `/api/report` endpoint accepts pre-computed results from the frontend. The past sessions sidebar loads stored outputs from SQLite via `/api/sessions/{id}`. Neither re-invokes the LangGraph pipeline, keeping response times fast and API costs zero for repeat views.

---

## 9. Directory Structure

```
ProspectIQ/
├── agents/
│   ├── __init__.py
│   ├── state.py                  # ProspectIQState TypedDict
│   ├── graph.py                  # LangGraph pipeline definition
│   ├── planner_agent.py
│   ├── icp_agent.py
│   ├── web_search_agent.py
│   ├── company_validation_agent.py
│   ├── decision_maker_agent.py
│   ├── contact_enrichment_agent.py
│   └── recommendation_agent.py
├── backend/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app + CORS + startup
│   ├── database.py               # SQLAlchemy models + CRUD
│   ├── models.py                 # Pydantic request/response models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── discovery.py          # All 5 API endpoints
│   └── services/
│       ├── __init__.py
│       └── pdf_service.py        # PyMuPDF 8-page report generator
├── frontend/
│   ├── app.py                    # Streamlit entry point
│   └── components/
│       ├── __init__.py
│       ├── upload_section.py     # Input form
│       ├── results_section.py    # 6-tab results dashboard
│       └── approval_section.py   # Human-in-the-loop buttons
├── config/
│   ├── __init__.py
│   └── settings.py               # API keys + model config
├── docs/
│   ├── architecture.md           # This file
│   └── diagrams/
│       └── architecture.png
├── tests/
│   ├── __init__.py
│   └── test_agents.py
├── sample_testcase/
│   └── prospectiq_sample_input_output.pdf
├── tools_used/
│   └── prospectiq_tools_and_technologies.pdf
├── prospectiq.db                 # SQLite database (auto-created)
└── requirements.txt
```

---

## 10. Running the System

```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
streamlit run frontend/app.py
```

The backend must be running before the frontend is loaded. The SQLite database is created automatically on first startup via `init_db()`.

---

*ProspectIQ · XLVentures.AI Hackathon 2025 · Powered by LangGraph | LLaMA 3.1 8B | Tavily | FastAPI | Streamlit | Groq*