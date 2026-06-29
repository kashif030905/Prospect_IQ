import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import requests
import time
from frontend.components.upload_section import render_input_section
from frontend.components.results_section import render_results_section, count_prospects
from frontend.components.approval_section import render_approval_section

st.set_page_config(
    page_title="ProspectIQ",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-30px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-8px); }
}
@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
}
.welcome-banner {
    border-radius: 20px;
    padding: 48px 40px;
    text-align: center;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    animation: fadeInDown 0.8s ease forwards;
}
[data-theme="light"] .welcome-banner {
    background: linear-gradient(135deg, #f7f9fc 0%, #edf2f7 50%, #f7f9fc 100%);
    border: 1px solid #e2e8f0;
}
[data-theme="dark"] .welcome-banner {
    background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 50%, #0f1117 100%);
    border: 1px solid #2d3250;
}
.welcome-banner::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 300%; height: 100%;
    background: linear-gradient(90deg,
        transparent 0%,
        rgba(79,139,249,0.05) 40%,
        rgba(79,139,249,0.1) 50%,
        rgba(79,139,249,0.05) 60%,
        transparent 100%);
    animation: shimmer 3s infinite;
}
.welcome-title {
    font-size: 52px;
    font-weight: 800;
    background: linear-gradient(135deg, #4f8bf9, #a78bfa, #4f8bf9);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 3s linear infinite;
    margin-bottom: 8px;
}
.welcome-subtitle {
    font-size: 18px;
    animation: fadeInUp 0.8s ease 0.3s both;
    margin-bottom: 24px;
}
[data-theme="light"] .welcome-subtitle { color: #4a5568; }
[data-theme="dark"]  .welcome-subtitle { color: #a0aec0; }
.welcome-tagline {
    font-size: 14px;
    animation: fadeInUp 0.8s ease 0.5s both;
}
[data-theme="light"] .welcome-tagline { color: #718096; }
[data-theme="dark"]  .welcome-tagline { color: #718096; }
.float-emoji {
    display: inline-block;
    font-size: 32px;
    animation: float 3s ease-in-out infinite;
    margin: 0 8px;
}
.float-emoji:nth-child(2) { animation-delay: 0.5s; }
.float-emoji:nth-child(3) { animation-delay: 1.0s; }
.float-emoji:nth-child(4) { animation-delay: 1.5s; }
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 28px;
    animation: fadeInUp 0.8s ease 0.6s both;
}
.stat-item { text-align: center; }
.stat-number { font-size: 28px; font-weight: 800; color: #4f8bf9; }
.stat-label  { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
[data-theme="light"] .stat-label { color: #718096; }
[data-theme="dark"]  .stat-label { color: #718096; }
.stMetric {
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
[data-theme="light"] .stMetric {
    background-color: #f7fafc;
    border: 1px solid #e2e8f0;
}
[data-theme="dark"] .stMetric {
    background-color: #1a1f2e;
    border: 1px solid #2d3250;
}
.stMetric:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(79,139,249,0.2);
    border-color: #4f8bf9;
}
[data-theme="light"] .stMetric label {
    color: #4a5568 !important;
}
[data-theme="dark"] .stMetric label {
    color: #a0aec0 !important;
}
.stMetric label {
    font-weight: 600 !important;
    font-size: 12px !important;
}
[data-theme="light"] .stMetric div[data-testid="stMetricValue"] {
    color: #1a202c !important;
}
[data-theme="dark"] .stMetric div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}
.stMetric div[data-testid="stMetricValue"] {
    font-size: 26px !important;
}
.pipeline-header {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 16px;
}
.stButton > button {
    border-radius: 10px;
    font-size: 16px;
    font-weight: bold;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79,139,249,0.35);
}
div[data-testid="stExpander"] {
    border-radius: 8px;
    transition: border-color 0.2s ease;
}
[data-theme="light"] div[data-testid="stExpander"] {
    border: 1px solid #e2e8f0;
}
[data-theme="dark"] div[data-testid="stExpander"] {
    border: 1px solid #2d3250;
}
div[data-testid="stExpander"]:hover {
    border-color: #4f8bf9;
}
.stTabs [data-baseweb="tab"] {
    font-size: 14px;
    font-weight: 600;
}
.glow-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #4f8bf9, transparent);
    margin: 24px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Welcome Banner ─────────────────────────────────────────
prospect_display = "0"
if "results" in st.session_state:
    prospect_display = str(count_prospects(st.session_state["results"]))

st.markdown(f"""
<div class="welcome-banner">
    <div class="welcome-title">🎯 ProspectIQ</div>
    <div class="welcome-subtitle">Reusable Agentic AI Platform for B2B Customer Discovery</div>
    <div>
        <span class="float-emoji">🤖</span>
        <span class="float-emoji">🔍</span>
        <span class="float-emoji">📬</span>
        <span class="float-emoji">🚀</span>
    </div>
    <div class="welcome-tagline">
        Powered by 7 AI Agents · Real Web Search · Human-in-the-Loop
    </div>
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-number">7</div>
            <div class="stat-label">AI Agents</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">20+</div>
            <div class="stat-label">Web Searches</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{prospect_display}</div>
            <div class="stat-label">Prospects Found</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">100%</div>
            <div class="stat-label">Real Data</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:10px 0;">
        <div style="font-size:40px;animation:float 3s ease-in-out infinite;">🎯</div>
        <div style="font-size:20px;font-weight:800;margin:6px 0;">ProspectIQ</div>
        <div style="font-size:12px;color:#718096;">Reusable Agentic AI Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Past Sessions ──────────────────────────────────────
    st.subheader("🗂️ Past Sessions")
    try:
        resp = requests.get("http://127.0.0.1:8000/api/sessions", timeout=5)
        if resp.status_code == 200:
            sessions = resp.json().get("sessions", [])
            if sessions:
                for s in sessions[:5]:
                    status_icon = "✅" if s["status"] == "approved" else "❌" if s["status"] == "rejected" else "🕐"
                    label = f"{status_icon} {s['target_industry']} · {s['target_location']}"
                    caption = s["created_at"]
                    with st.expander(label):
                        st.caption(caption)
                        st.write(f"**Role:** {s['target_persona']}")
                        st.write(f"**Size:** {s['company_size']}")
                        st.write(f"**Product:** {s['product_description'][:80]}...")
                        if st.button("Load this session", key=f"load_{s['id']}"):
                            detail = requests.get(
                                f"http://127.0.0.1:8000/api/sessions/{s['id']}",
                                timeout=5
                            ).json().get("session", {})
                            st.session_state["results"] = {
                                "plan":                detail.get("plan"),
                                "icp_profile":         detail.get("icp_profile"),
                                "companies_found":     detail.get("companies_found"),
                                "validated_companies": detail.get("validated_companies"),
                                "decision_makers":     detail.get("decision_makers"),
                                "enriched_contacts":   detail.get("enriched_contacts"),
                                "recommendations":     detail.get("recommendations"),
                            }
                            st.session_state["user_inputs"] = {
                                "product_description": detail.get("product_description"),
                                "target_industry":     detail.get("target_industry"),
                                "target_company_size": detail.get("company_size"),
                                "target_role":         detail.get("target_persona"),
                                "target_location":     detail.get("target_location"),
                            }
                            st.rerun()
            else:
                st.caption("No past sessions yet. Run a discovery to save one.")
        else:
            st.caption("Could not load sessions.")
    except Exception:
        st.caption("Backend offline — past sessions unavailable.")

    st.divider()

    st.subheader("🤖 AI Agents")
    agents_info = {
        "📋 Planner Agent":        "Reads your ICP and creates a structured discovery plan.",
        "🧩 ICP Agent":            "Defines your Ideal Customer Profile with qualification criteria.",
        "🌐 Web Search Agent":     "Searches the web for companies matching your ICP.",
        "✅ Validation Agent":     "Validates each company against your size, industry, and location.",
        "👤 Decision Maker Agent": "Finds the right person to contact inside each company.",
        "📬 Enrichment Agent":     "Finds LinkedIn profiles and emails for each decision maker.",
        "🎯 Recommendation Agent": "Picks the best prospect and suggests the outreach approach."
    }
    for agent, explanation in agents_info.items():
        with st.expander(agent):
            st.caption(explanation)

    st.divider()
    st.subheader("ℹ️ System Info")
    st.write("**Model:** LLaMA 3.1 8B")
    st.write("**Framework:** LangGraph")
    st.write("**Backend:** FastAPI")
    st.write("**Version:** 2.0.0")

# ── Agent Pipeline ─────────────────────────────────────────
st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="pipeline-header">🔄 Agent Pipeline</div>', unsafe_allow_html=True)

PIPELINE = [
    ("📋", "Planner"),
    ("🧩", "ICP"),
    ("🌐", "Web Search"),
    ("✅", "Validation"),
    ("👤", "Decision Maker"),
    ("📬", "Enrichment"),
    ("🎯", "Recommendation"),
]

def render_pipeline():
    cols = st.columns(len(PIPELINE))
    agent_status = st.session_state.get("agent_status", {})
    for col, (icon, name) in zip(cols, PIPELINE):
        with col:
            if agent_status.get(name) == "done":
                st.metric(label=f"✅ {name}", value=icon)
            elif agent_status.get(name) == "running":
                st.metric(label=f"⏳ {name}", value="🔄")
            else:
                st.metric(label=name, value=icon)

pipeline_placeholder = st.empty()
with pipeline_placeholder.container():
    render_pipeline()

# ── Input Section ──────────────────────────────────────────
st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
user_inputs = render_input_section()
st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ── Analyze Button ─────────────────────────────────────────
if user_inputs:
    if st.button("🚀 Start Customer Discovery", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_box   = st.empty()

        STEPS = [
            ("Planner",        10, "📋 Planner Agent creating discovery plan..."),
            ("ICP",            20, "🧩 ICP Agent defining ideal customer profile..."),
            ("Web Search",     35, "🌐 Web Search Agent finding matching companies..."),
            ("Validation",     50, "✅ Validation Agent checking each company..."),
            ("Decision Maker", 65, "👤 Decision Maker Agent finding contacts..."),
            ("Enrichment",     80, "📬 Enrichment Agent finding emails & LinkedIn..."),
            ("Recommendation", 90, "🎯 Recommendation Agent finalising best prospect..."),
        ]

        def mark(name, state):
            st.session_state["agent_status"] = {
                **st.session_state.get("agent_status", {}),
                name: state
            }
            with pipeline_placeholder.container():
                render_pipeline()

        for name, pct, msg in STEPS[:4]:
            mark(name, "running")
            status_box.info(f"⚙️ {msg}")
            progress_bar.progress(pct)
            time.sleep(0.8)
            mark(name, "done")

        mark("Decision Maker", "running")
        status_box.info("👤 Decision Maker Agent finding contacts... *(this may take 2–3 minutes)*")
        progress_bar.progress(65)

        try:
            response = requests.post(
                "http://127.0.0.1:8000/api/analyze",
                json=user_inputs,
                timeout=600
            )

            mark("Decision Maker", "done")
            mark("Enrichment", "running")
            status_box.info("📬 Enrichment Agent finding emails & LinkedIn...")
            progress_bar.progress(80)
            time.sleep(0.8)
            mark("Enrichment", "done")
            mark("Recommendation", "running")
            status_box.info("🎯 Recommendation Agent finalising best prospect...")
            progress_bar.progress(90)
            time.sleep(0.8)
            mark("Recommendation", "done")

            if response.status_code == 200:
                results = response.json()
                progress_bar.progress(100)
                st.session_state["results"]     = results
                st.session_state["user_inputs"] = user_inputs
                st.session_state["session_id"]  = results.get("session_id")
                status_box.success("✅ All agents completed! Scroll down to see your prospects.")
                st.snow()
                time.sleep(1)
                st.rerun()
            else:
                status_box.error(f"Backend error: {response.text}")

        except requests.exceptions.Timeout:
            status_box.error("⏱️ Timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            status_box.error("❌ Cannot connect to backend. Run: uvicorn backend.main:app --reload --port 8000")
        except Exception as e:
            status_box.error(f"Something went wrong: {str(e)}")

elif not user_inputs:
    st.info("👆 Fill in all the fields above to unlock the discovery button.")

# ── Results ────────────────────────────────────────────────
if "results" in st.session_state:
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    render_results_section(st.session_state["results"])
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    st.subheader("📥 Download Report")
    inputs  = st.session_state.get("user_inputs", {})
    results = st.session_state["results"]

    @st.cache_data(show_spinner=False, ttl=3600)
    def _generate_pdf(_results_json: str, product: str, industry: str, size: str, role: str, location: str):
        resp = requests.post(
            "http://127.0.0.1:8000/api/report",
            json={
                "product_description": product,
                "target_industry":     industry,
                "target_company_size": size,
                "target_role":         role,
                "target_location":     location,
                "results":             json.loads(_results_json),
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content

    try:
        with st.spinner("Preparing PDF report..."):
            pdf_bytes = _generate_pdf(
                json.dumps(results, sort_keys=True),
                inputs.get("product_description", ""),
                inputs.get("target_industry", ""),
                inputs.get("target_company_size", ""),
                inputs.get("target_role", ""),
                inputs.get("target_location", "Not specified"),
            )
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name="prospectiq_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        st.caption("Make sure the backend is running on port 8000.")

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    render_approval_section()