# 🎯 ProspectIQ — Agentic AI Platform for B2B Customer Discovery

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-0.4.8-green?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45-FF4B4B?style=for-the-badge&logo=streamlit)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1_8B-orange?style=for-the-badge)
![Tavily](https://img.shields.io/badge/Tavily-Web_Search-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

> **An Agentic AI Platform where 7 specialized AI agents collaborate to automate B2B customer discovery, contact enrichment, and sales playbook generation.**

Built for the **XLVentures.AI Hackathon** — focused on Agentic AI Platform Architecture.

---

## 📌 Table of Contents

- [Business Problem](#-business-problem)
- [Solution](#-solution)
- [Architecture](#-architecture)
- [AI Agents](#-ai-agents)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Setup Instructions](#-setup-instructions)
- [API Endpoints](#-api-endpoints)
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Team](#-team)

---

## 💼 Business Problem

Every B2B SaaS company faces this challenge:

- Sales teams spend **days manually researching** companies that might be a good fit
- They waste time chasing **leads that don't match** their Ideal Customer Profile
- Finding the **right decision maker** inside a target company is time-consuming and inconsistent
- There is **no systematic way** to discover, validate, and enrich prospects at scale

**Result:** Slow pipeline building, wasted outreach effort, and missed revenue opportunities.

---

## ✅ Solution

**ProspectIQ** is an Agentic AI Platform that acts as a **virtual sales development team**.

Enter your product, target industry, company size, decision maker role, and location → 7 AI agents automatically find real companies, validate them against your ICP, identify decision makers, enrich contact details, and deliver a ready-to-execute sales playbook — all in minutes.

A **Human-in-the-Loop** approval step ensures the sales manager stays in control before outreach begins.

---

## 🏗️ Architecture

![ProspectIQ Architecture](docs/diagrams/architecture.png)

---

## 🤖 AI Agents

ProspectIQ uses **7 specialized AI agents** orchestrated by LangGraph, each with a specific role:

| # | Agent | Role | Input | Output |
|---|-------|------|-------|--------|
| 1 | 📋 **Planner Agent** | Creates a location-specific discovery strategy | User inputs | Structured discovery plan |
| 2 | 🧩 **ICP Agent** | Defines the Ideal Customer Profile with qualification criteria | Plan + user inputs | Detailed ICP profile |
| 3 | 🌐 **Web Search Agent** | Runs parallel Tavily searches to find real matching companies | ICP profile | Verified company list |
| 4 | ✅ **Validation Agent** | Scores each company /100; location is a hard disqualifier | Companies found | Scored & ranked companies |
| 5 | 👤 **Decision Maker Agent** | Finds the right contact inside each shortlisted company | Validated companies | Decision maker profiles |
| 6 | 📬 **Enrichment Agent** | Finds emails, LinkedIn profiles, hooks, and email templates | Decision makers | Enriched contact cards |
| 7 | 🎯 **Recommendation Agent** | Synthesises everything into a final ranked sales playbook | All agent outputs | Actionable sales playbook |

### 🧠 Shared Memory (LangGraph State)

All agents communicate through a **shared state** (`ProcureAIState`) — a typed dictionary that acts like a shared workspace:

```python
class ProcureAIState(TypedDict):
    # User inputs
    product_description: str        # What the SaaS product does
    target_industry: str            # Which industry to target
    company_size: str               # Target company size
    target_persona: str             # Who to contact (CEO, CTO etc.)
    target_location: str            # Target geography (e.g. Mumbai, India)

    # Agent outputs
    plan: Optional[str]             # Planner Agent output
    icp_profile: Optional[str]      # ICP Agent output
    companies_found: Optional[str]  # Web Search Agent output
    validated_companies: Optional[str]  # Validation Agent output
    decision_makers: Optional[str]  # Decision Maker Agent output
    enriched_contacts: Optional[str]  # Contact Enrichment Agent output
    recommendations: Optional[str]  # Recommendation Agent output

    # Human in the loop
    human_approved: Optional[bool]
```

Each agent **reads** from this state and **writes** its output back — no agent talks directly to another. This is clean, scalable, and fully extensible.

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13 | Core language |
| **LangGraph** | 0.4.8 | Multi-agent orchestration & state management |
| **LangChain** | 0.3.25 | LLM integration layer |
| **LangChain-Groq** | latest | Groq API connector |
| **LLaMA 3.1 8B** | via Groq | AI model — 500k tokens/day free tier |
| **Tavily** | latest | Real-time web search for company discovery |
| **FastAPI** | 0.115 | REST API backend |
| **Streamlit** | 1.45 | Frontend UI |
| **PyMuPDF** | 1.25.5 | PDF report generation |
| **Pydantic** | 2.11.4 | Data validation |
| **Uvicorn** | 0.34.3 | ASGI server |

---

## 📁 Project Structure

```
prospectiq/
│
├── agents/                          # All AI agents
│   ├── state.py                     # Shared memory (ProcureAIState)
│   ├── graph.py                     # LangGraph pipeline wiring
│   ├── planner_agent.py             # Agent 1: Discovery strategy
│   ├── icp_agent.py                 # Agent 2: Ideal Customer Profile
│   ├── web_search_agent.py          # Agent 3: Parallel Tavily search
│   ├── company_validation_agent.py  # Agent 4: Score & filter companies
│   ├── decision_maker_agent.py      # Agent 5: Find right contacts
│   ├── contact_enrichment_agent.py  # Agent 6: Enrich contact details
│   └── recommendation_agent.py     # Agent 7: Final sales playbook
│
├── backend/                         # FastAPI backend
│   ├── main.py                      # App entry point + CORS
│   ├── routes/
│   │   └── discovery.py             # API route handlers
│   └── services/
│       └── pdf_service.py           # 8-page PDF report generation
│
├── frontend/                        # Streamlit UI
│   ├── app.py                       # Main UI application
│   └── components/
│       ├── upload_section.py        # Input form component
│       ├── results_section.py       # 6-tab results dashboard
│       └── approval_section.py      # Human approval component
│
├── config/
│   └── settings.py                  # API keys and configuration
│
├── tests/
│   └── test_agents.py               # Test suite
│
├── docs/
│   └── diagrams/
│       └── architecture.png         # Architecture diagram
│
├── sample_data/                     # Sample inputs for testing
├── requirements.txt                 # Python dependencies
├── .env                             # API keys (not committed)
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.13
- A free [Groq API key](https://console.groq.com)
- A free [Tavily API key](https://tavily.com)

### 1. Clone the repository
```bash
git clone https://github.com/kashif030905/Procure_AI.git
cd Procure_AI
```

### 2. Create virtual environment
```bash
python3.13 -m venv venv
source venv/bin/activate       # Mac/Linux
# venv\Scripts\activate        # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
# Create .env file
cp .env.example .env

# Add your API keys
GROQ_API_KEY=your-groq-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here
GROQ_MODEL=llama-3.1-8b-instant
```

### 5. Run the backend (Terminal 1)
```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Run the frontend (Terminal 2)
```bash
streamlit run frontend/app.py
```

### 7. Open the app
```
http://localhost:8501
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/analyze` | Run the full 7-agent discovery pipeline |
| `POST` | `/api/approve` | Human approval decision (true/false) |
| `POST` | `/api/report` | Generate and download PDF sales playbook |

### Example: Run discovery
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Cloud-based project management software",
    "target_industry": "IT and Software",
    "target_company_size": "50-200 employees",
    "target_role": "CTO",
    "target_location": "Mumbai, India"
  }'
```

### Example response
```json
{
  "status": "success",
  "icp_profile": "...",
  "companies_found": "...",
  "validated_companies": "...",
  "decision_makers": "...",
  "enriched_contacts": "...",
  "recommendations": "..."
}
```

---

## ✨ Features

- 🎯 **ICP-Driven Discovery** — Define your Ideal Customer Profile and let agents do the research
- 🤖 **7 Specialized AI Agents** — Each agent has a distinct role and expertise
- 🧠 **Shared Memory** — LangGraph state connects all agents seamlessly
- 🌐 **Real Web Search** — Tavily API finds actual companies, not hallucinated ones
- ✅ **Location Hard Filter** — Companies outside your target location are automatically disqualified
- 👤 **Decision Maker Finder** — Identifies the right contact inside each shortlisted company
- 📬 **Contact Enrichment** — Email patterns, LinkedIn profiles, personalized hooks and templates
- 🎯 **Ranked Sales Playbook** — Final recommendation with prioritised prospect list and 14-day outreach sequence
- 👤 **Human-in-the-Loop** — Sales manager approves or rejects before outreach begins
- 📥 **PDF Report** — Full 8-page discovery report downloadable as PDF
- 🔄 **Extensible Architecture** — New agents can be added in minutes

---

## ⚙️ How It Works

1. **Input** — Sales rep enters product description, target industry, company size, decision maker role, and location
2. **Plan** — Planner Agent creates a location-specific discovery strategy
3. **ICP** — ICP Agent defines the Ideal Customer Profile with hard and soft qualification criteria
4. **Search** — Web Search Agent runs 5 parallel Tavily queries to find real matching companies
5. **Validate** — Validation Agent scores each company /100; any company outside the target location scores 0
6. **Decision Makers** — Decision Maker Agent searches LinkedIn and the web to find the right contact at each shortlisted company
7. **Enrich** — Enrichment Agent finds emails, LinkedIn profiles, personalized hooks, and email templates for each contact
8. **Recommend** — Recommendation Agent synthesises everything into a ranked playbook with a 14-day outreach sequence
9. **Approve** — Sales manager reviews the results across 6 dashboard tabs and approves or rejects
10. **Report** — Full discovery report downloaded as a professional PDF

---

## 👥 Team

Built for **XLVentures.AI Hackathon 2026**

| Name | Role |
|------|------|
| Syed Kashif Uddin| AI Engineer |
| Sphoorthy Nidasanametla | Backend Engineer |
| Sriprada Yegoti | Frontend Engineer |

---

## 📄 License

MIT License — feel free to use, modify, and build on this project.

---

<div align="center">
  <strong>Built using LangGraph, FastAPI, and Streamlit</strong>
</div>