import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
from frontend.components.upload_section import render_upload_section
from frontend.components.results_section import render_results_section
from frontend.components.approval_section import render_approval_section

# Page configuration
st.set_page_config(
    page_title="ProcureAI",
    page_icon="🤖",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot.png", width=80)
    st.title("ProcureAI")
    st.caption("Agentic Procurement Intelligence Platform")
    st.divider()

    st.subheader("🤖 AI Agents")
    agents = [
        "📋 Planner Agent",
        "📄 Document Agent",
        "🔍 Comparison Agent",
        "⚠️ Risk Agent",
        "🤝 Negotiation Agent",
        "✅ Recommendation Agent"
    ]
    for agent in agents:
        st.write(agent)

    st.divider()
    st.subheader("ℹ️ System Info")
    st.write("**Model:** LLaMA 3.3 70B")
    st.write("**Framework:** LangGraph")
    st.write("**Backend:** FastAPI")
    st.write("**Version:** 1.0.0")

# Main content
st.title("🤖 ProcureAI")
st.subheader("Agentic Procurement Intelligence Platform")
st.write("Upload vendor quotations and let our AI agents analyze, compare, and recommend the best vendor.")
st.divider()

# Agent pipeline visualization
st.subheader("🔄 Agent Pipeline")
cols = st.columns(6)
pipeline = [
    ("📋", "Planner"),
    ("📄", "Document"),
    ("🔍", "Comparison"),
    ("⚠️", "Risk"),
    ("🤝", "Negotiation"),
    ("✅", "Recommendation")
]
for col, (icon, name) in zip(cols, pipeline):
    with col:
        st.metric(label=name, value=icon)

st.divider()

# Upload Section
uploaded_files = render_upload_section()
st.divider()

# Analyze Button
if uploaded_files and len(uploaded_files) >= 2:
    if st.button("🚀 Start AI Analysis", type="primary", use_container_width=True):
        # Show agent progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("🤖 AI Agents are analyzing your quotations..."):
            try:
                status_text.write("📋 Planner Agent creating analysis plan...")
                progress_bar.progress(10)

                files = [
                    ("files", (file.name, file.getvalue(), "application/pdf"))
                    for file in uploaded_files
                ]

                status_text.write("📄 Document Agent extracting information...")
                progress_bar.progress(30)

                response = requests.post(
                    "http://127.0.0.1:8000/api/analyze",
                    files=files
                )

                status_text.write("🔍 Comparison Agent comparing vendors...")
                progress_bar.progress(50)

                if response.status_code == 200:
                    results = response.json()

                    status_text.write("⚠️ Risk Agent analyzing risks...")
                    progress_bar.progress(70)

                    status_text.write("🤝 Negotiation Agent preparing strategies...")
                    progress_bar.progress(85)

                    status_text.write("✅ Recommendation Agent finalizing decision...")
                    progress_bar.progress(100)

                    st.session_state["results"] = results
                    status_text.write("✅ Analysis complete!")
                    st.success("All agents completed successfully!")
                else:
                    st.error(f"Error: {response.text}")

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

elif uploaded_files and len(uploaded_files) < 2:
    st.warning("⚠️ Please upload at least 2 vendor quotations to compare.")

# Show Results
if "results" in st.session_state:
    st.divider()
    render_results_section(st.session_state["results"])
    st.divider()
    render_approval_section()