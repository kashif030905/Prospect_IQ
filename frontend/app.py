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

# Header
st.title("🤖 ProcureAI")
st.subheader("Agentic Procurement Intelligence Platform")
st.write("Powered by multiple AI agents working together to make smarter procurement decisions.")
st.divider()

# Step 1: Upload Section
uploaded_files = render_upload_section()
st.divider()

# Step 2: Analyze Button
if uploaded_files and len(uploaded_files) >= 2:
    if st.button("🚀 Start AI Analysis", type="primary", use_container_width=True):
        with st.spinner("🤖 AI Agents are analyzing your quotations... This may take 30-60 seconds."):
            try:
                # Prepare files for the API call
                files = [
                    ("files", (file.name, file.getvalue(), "application/pdf"))
                    for file in uploaded_files
                ]

                # Call the FastAPI backend
                response = requests.post(
                    "http://127.0.0.1:8000/api/analyze",
                    files=files
                )

                if response.status_code == 200:
                    results = response.json()
                    st.session_state["results"] = results
                    st.success("✅ Analysis complete!")
                else:
                    st.error(f"Error: {response.text}")

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

elif uploaded_files and len(uploaded_files) < 2:
    st.warning("⚠️ Please upload at least 2 vendor quotations to compare.")

# Step 3: Show Results if available
if "results" in st.session_state:
    st.divider()
    render_results_section(st.session_state["results"])
    st.divider()
    render_approval_section()