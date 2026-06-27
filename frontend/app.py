import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests

from frontend.components.upload_section import render_input_section
from frontend.components.results_section import render_results_section
from frontend.components.approval_section import render_approval_section

st.set_page_config(
    page_title="ProcureAI",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
    <style>
    .stMetric {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
    .stMetric label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    .stButton > button {
        border-radius: 8px;
        padding: 12px;
        font-size: 16px;
        font-weight: bold;
    }
    .input-card {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot.png", width=80)
    st.title("ProcureAI")
    st.caption("Agentic Customer Discovery Platform")
    st.divider()

    st.subheader("🤖 AI Agents")

    agents_info = {
        "📋 Planner Agent": "Reads your product and ICP, creates a structured discovery plan.",
        "🌐 Web Search Agent": "Searches the web for companies matching your ideal customer profile.",
        "✅ Validation Agent": "Checks each company against your size, industry, and location criteria.",
        "👤 Decision Maker Agent": "Finds the right person to contact inside each validated company.",
        "📬 Enrichment Agent": "Finds LinkedIn profiles and email addresses for each decision maker.",
        "🎯 Recommendation Agent": "Picks the best prospect and suggests the ideal outreach approach."
    }

    for agent, explanation in agents_info.items():
        with st.expander(agent):
            st.caption(explanation)

    st.divider()
    st.subheader("ℹ️ System Info")
    # FIX #2: Corrected model name to match settings.py (was "LLaMA 3.3 70B")
    st.write("**Model:** LLaMA 3.1 8B Instant")
    st.write("**Framework:** LangGraph")
    st.write("**Backend:** FastAPI")
    # FIX #3: Corrected version to match main.py and settings.py (was "1.0.0")
    st.write("**Version:** 2.0.0")

# Main Header
st.title("🤖 ProcureAI")
st.subheader("Agentic Customer Discovery Platform")
st.write("Enter your product details and let our AI agents find, validate, and recommend your best sales prospects.")
st.divider()

# Agent Pipeline
st.subheader("🔄 Agent Pipeline")
cols = st.columns(6)
pipeline = [
    ("📋", "Planner"),
    ("🌐", "Web Search"),
    ("✅", "Validation"),
    ("👤", "Decision Maker"),
    ("📬", "Enrichment"),
    ("🎯", "Recommendation")
]

agent_status = st.session_state.get("agent_status", {})
for col, (icon, name) in zip(cols, pipeline):
    with col:
        if agent_status.get(name) == "done":
            st.metric(label=f"✅ {name}", value=icon)
        elif agent_status.get(name) == "running":
            st.metric(label=f"⏳ {name}", value=icon)
        else:
            st.metric(label=name, value=icon)

st.divider()

# Input Section
user_inputs = render_input_section()
st.divider()

# Analyze Button
if user_inputs:
    if st.button("🚀 Start Customer Discovery", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.write("📋 Planner Agent creating discovery plan...")
            progress_bar.progress(15)

            response = requests.post(
                "http://127.0.0.1:8000/api/analyze",
                json=user_inputs
            )

            if response.status_code == 200:
                results = response.json()

                status_text.write("🌐 Web Search Agent finding companies...")
                progress_bar.progress(30)

                status_text.write("✅ Validation Agent checking criteria...")
                progress_bar.progress(50)

                status_text.write("👤 Decision Maker Agent finding contacts...")
                progress_bar.progress(65)

                status_text.write("📬 Enrichment Agent finding emails and LinkedIn...")
                progress_bar.progress(80)

                status_text.write("🎯 Recommendation Agent finalizing best prospect...")
                progress_bar.progress(95)

                st.session_state["agent_status"] = {
                    "Planner": "done",
                    "Web Search": "done",
                    "Validation": "done",
                    "Decision Maker": "done",
                    "Enrichment": "done",
                    "Recommendation": "done"
                }

                progress_bar.progress(100)
                st.session_state["results"] = results
                st.session_state["user_inputs"] = user_inputs
                status_text.write("✅ All agents completed!")
                st.success("Customer discovery complete!")
                st.rerun()

            else:
                st.error(f"Error: {response.text}")

        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")

elif not user_inputs:
    st.info("👆 Fill in all fields above to start customer discovery.")

# Show Results
if "results" in st.session_state:
    st.divider()
    render_results_section(st.session_state["results"])
    st.divider()

    # Download Report — Professional PDF
    st.subheader("📥 Download Report")
    inputs = st.session_state.get("user_inputs", {})

    if st.button("📄 Generate & Download PDF Report", type="secondary", use_container_width=True):
        with st.spinner("Generating professional PDF report..."):
            try:
                pdf_response = requests.post(
                    "http://127.0.0.1:8000/api/report",
                    json=inputs
                )
                if pdf_response.status_code == 200:
                    st.download_button(
                        label="📥 Click Here to Download PDF",
                        data=pdf_response.content,
                        file_name="procureai_discovery_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF report ready!")
                else:
                    st.error(f"PDF generation failed: {pdf_response.text}")
            except Exception as e:
                st.error(f"Could not generate PDF: {str(e)}")

    st.divider()
    render_approval_section()