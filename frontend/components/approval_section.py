import streamlit as st
import requests

def render_approval_section():
    st.header("👤 Human Approval Required")
    st.warning("Please review the recommended contacts above before taking any action.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve & Proceed to Outreach", type="primary", use_container_width=True):
            response = requests.post(
                "http://127.0.0.1:8000/api/approve",
                params={"approved": True}
            )
            if response.status_code == 200:
                st.success("✅ Approved! Your sales team can now proceed with outreach.")
                st.balloons()

    with col2:
        if st.button("❌ Reject & Refine Search", type="secondary", use_container_width=True):
            response = requests.post(
                "http://127.0.0.1:8000/api/approve",
                params={"approved": False}
            )
            if response.status_code == 200:
                st.error("❌ Rejected. Please refine your target criteria and try again.")