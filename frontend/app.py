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

# Custom CSS
st.markdown("""
    <style>
    .stMetric {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
    .stButton > button {
        border-radius: 8px;
        padding: 12px;
        font-size: 16px;
        font-weight: bold;
    }
    .vendor-card {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .agent-card {
        background-color: #1e2130;
        border-left: 4px solid #4f8bf9;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .metric-card {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 5px 0;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4f8bf9;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #888;
        margin-top: 4px;
    }
    .result-box {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        line-height: 1.7;
    }
    .result-header {
        font-size: 1.1rem;
        font-weight: bold;
        color: #4f8bf9;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #2d3250;
    }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot.png", width=80)
    st.title("ProcureAI")
    st.caption("Agentic Procurement Intelligence Platform")
    st.divider()

    st.subheader("🤖 AI Agents")

    agents_info = {
        "📋 Planner Agent": "Receives the task and creates a structured analysis plan for all other agents.",
        "📄 Document Agent": "Reads each vendor PDF and extracts key information like price, delivery, and terms.",
        "🔍 Comparison Agent": "Compares all vendors side by side across price, delivery, warranty, and support.",
        "⚠️ Risk Agent": "Identifies hidden risks, unfavorable clauses, and red flags in each quotation.",
        "🤝 Negotiation Agent": "Suggests specific negotiation tactics and leverage points for each vendor.",
        "✅ Recommendation Agent": "Reads all analysis and recommends the best vendor with clear reasoning."
    }

    for agent, explanation in agents_info.items():
        with st.expander(agent):
            st.caption(explanation)

    st.divider()
    st.subheader("ℹ️ System Info")
    st.write("**Model:** LLaMA 3.3 70B")
    st.write("**Framework:** LangGraph")
    st.write("**Backend:** FastAPI")
    st.write("**Version:** 1.0.0")

# ── Main Header ───────────────────────────────────────────────────────────────
st.title("🤖 ProcureAI")
st.subheader("Agentic Procurement Intelligence Platform")
st.write("Upload vendor quotations and let our AI agents analyze, compare, and recommend the best vendor.")
st.divider()

# ── Agent Pipeline ────────────────────────────────────────────────────────────
st.subheader("🔄 Agent Pipeline")

pipeline = [
    ("📋", "Planner"),
    ("📄", "Document"),
    ("🔍", "Comparison"),
    ("⚠️", "Risk"),
    ("🤝", "Negotiation"),
    ("✅", "Recommendation")
]

agent_status = st.session_state.get("agent_status", {})
cols = st.columns(6)
for col, (icon, name) in zip(cols, pipeline):
    with col:
        status = agent_status.get(name, "idle")
        if status == "done":
            st.markdown(f"""
            <div style="background:#0e3d2e;border:1px solid #1a6b4a;border-radius:10px;
                        padding:12px;text-align:center;">
                <div style="font-size:1.5rem">{icon}</div>
                <div style="color:#2ecc71;font-size:0.8rem;font-weight:bold">✅ {name}</div>
            </div>
            """, unsafe_allow_html=True)
        elif status == "running":
            st.markdown(f"""
            <div style="background:#2d2a0e;border:1px solid #6b5a1a;border-radius:10px;
                        padding:12px;text-align:center;">
                <div style="font-size:1.5rem">⏳</div>
                <div style="color:#f1c40f;font-size:0.8rem;font-weight:bold">Running...</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#1e2130;border:1px solid #2d3250;border-radius:10px;
                        padding:12px;text-align:center;">
                <div style="font-size:1.5rem">{icon}</div>
                <div style="color:#888;font-size:0.8rem">{name}</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Upload Section ────────────────────────────────────────────────────────────
uploaded_files = render_upload_section()

# ── Vendor Cards ──────────────────────────────────────────────────────────────
if uploaded_files:
    st.subheader("📦 Uploaded Vendors")
    cols_per_row = 4
    for row_start in range(0, len(uploaded_files), cols_per_row):
        row_files = uploaded_files[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for i, (col, file) in enumerate(zip(cols, row_files)):
            with col:
                st.markdown(f"""
                <div class='vendor-card'>
                    <h4>Vendor {row_start + i + 1}</h4>
                    <p>📄 {file.name}</p>
                    <p>📦 {round(file.size/1024, 1)} KB</p>
                </div>
                """, unsafe_allow_html=True)

st.divider()

# ── Analyze Button with Live Agent Animation ──────────────────────────────────
if uploaded_files and len(uploaded_files) >= 2:
    if st.button("🚀 Start AI Analysis", type="primary", use_container_width=True):

        progress_bar = st.progress(0)
        status_text = st.empty()
        pipeline_placeholder = st.empty()

        def update_pipeline(done_agents, running_agent=None):
            cols_html = ""
            for icon, name in pipeline:
                if name in done_agents:
                    cols_html += f"""
                    <div style="background:#0e3d2e;border:1px solid #1a6b4a;border-radius:10px;
                                padding:12px;text-align:center;flex:1;margin:0 4px">
                        <div style="font-size:1.5rem">{icon}</div>
                        <div style="color:#2ecc71;font-size:0.75rem;font-weight:bold">✅ {name}</div>
                    </div>"""
                elif name == running_agent:
                    cols_html += f"""
                    <div style="background:#2d2a0e;border:1px solid #6b5a1a;border-radius:10px;
                                padding:12px;text-align:center;flex:1;margin:0 4px">
                        <div style="font-size:1.5rem">⏳</div>
                        <div style="color:#f1c40f;font-size:0.75rem;font-weight:bold">Running...</div>
                    </div>"""
                else:
                    cols_html += f"""
                    <div style="background:#1e2130;border:1px solid #2d3250;border-radius:10px;
                                padding:12px;text-align:center;flex:1;margin:0 4px">
                        <div style="font-size:1.5rem">{icon}</div>
                        <div style="color:#888;font-size:0.75rem">{name}</div>
                    </div>"""
            pipeline_placeholder.markdown(
                f'<div style="display:flex;gap:8px;margin:8px 0">{cols_html}</div>',
                unsafe_allow_html=True
            )

        try:
            files_payload = [
                ("files", (file.name, file.getvalue(), "application/pdf"))
                for file in uploaded_files
            ]

            import threading, time

            result_holder = {}
            error_holder = {}

            def call_api():
                try:
                    resp = requests.post(
                        "http://127.0.0.1:8000/api/analyze",
                        files=files_payload,
                        timeout=300
                    )
                    result_holder["resp"] = resp
                except Exception as ex:
                    error_holder["err"] = str(ex)

            thread = threading.Thread(target=call_api)
            thread.start()

            done = []
            steps = [
                ("Planner",        "📋 Planner Agent creating analysis plan...",      15),
                ("Document",       "📄 Document Agent extracting information...",      30),
                ("Comparison",     "🔍 Comparison Agent comparing vendors...",         50),
                ("Risk",           "⚠️ Risk Agent analyzing risks...",                65),
                ("Negotiation",    "🤝 Negotiation Agent preparing strategies...",     80),
                ("Recommendation", "✅ Recommendation Agent finalizing decision...",   95),
            ]

            for agent_name, msg, prog in steps:
                update_pipeline(done, running_agent=agent_name)
                status_text.write(msg)
                progress_bar.progress(prog)
                time.sleep(1.2)
                done.append(agent_name)

            thread.join()

            if "err" in error_holder:
                st.error(f"Something went wrong: {error_holder['err']}")
            else:
                resp = result_holder["resp"]
                if resp.status_code == 200:
                    results = resp.json()
                    update_pipeline(done)
                    progress_bar.progress(100)
                    status_text.write("✅ All agents completed!")

                    st.session_state["agent_status"] = {n: "done" for _, n in pipeline}
                    st.session_state["results"] = results
                    st.session_state["uploaded_files"] = uploaded_files
                    st.success("Analysis complete!")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.text}")

        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")

elif uploaded_files and len(uploaded_files) < 2:
    st.warning("⚠️ Please upload at least 2 vendor quotations to compare.")

# ── Results ───────────────────────────────────────────────────────────────────
if "results" in st.session_state:
    results = st.session_state["results"]
    st.divider()

    # ── Metrics Bar ───────────────────────────────────────────────────────────
    st.subheader("📊 Analysis Summary")

    saved_files = st.session_state.get("uploaded_files", uploaded_files or [])
    num_vendors = len(saved_files) if saved_files else "—"

    risk_text = results.get("risks", "")
    risk_count = risk_text.lower().count("high") + risk_text.lower().count("medium")

    rec_text = results.get("recommendation", "")
    rec_vendor = "—"
    for line in rec_text.split("\n"):
        if "recommended vendor" in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                rec_vendor = parts[1].strip().split()[0] if parts[1].strip() else "—"
            break

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{num_vendors}</div>
            <div class="metric-label">Vendors Analyzed</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">6</div>
            <div class="metric-label">AI Agents Used</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{risk_count}</div>
            <div class="metric-label">Risks Detected</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.4rem">{rec_vendor}</div>
            <div class="metric-label">Recommended Vendor</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Formatted Results ─────────────────────────────────────────────────────
    render_results_section(results)
    st.divider()

    # ── PDF Report Download (no extra LLM calls) ──────────────────────────────
    st.subheader("📥 Download Report")

    if st.button("📥 Generate & Download PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating professional PDF report..."):
            try:
                saved_files = st.session_state.get("uploaded_files", [])
                vendor_names = [f.name.replace(".pdf", "") for f in saved_files]

                report_response = requests.post(
                    "http://127.0.0.1:8000/api/report-from-results",
                    json={
                        "vendor_names": vendor_names,
                        "results": st.session_state["results"]
                    }
                )
                if report_response.status_code == 200:
                    st.download_button(
                        label="📄 Click here to save your PDF",
                        data=report_response.content,
                        file_name="procureai_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF report ready!")
                else:
                    st.error(f"Failed to generate report: {report_response.text}")
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

    st.divider()
    render_approval_section()