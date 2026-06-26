import streamlit as st
import requests

def render_approval_section():
    """
    Renders the Human-in-the-Loop approval section.
    Allows the procurement manager to approve or reject the recommendation.
    """
    st.header("👤 Human Approval Required")
    st.warning("Please review the recommendation above and make your decision.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve Recommendation", type="primary", use_container_width=True):
            response = requests.post(
                "http://127.0.0.1:8000/api/approve",
                params={"approved": True}
            )
            if response.status_code == 200:
                st.success("✅ Recommendation Approved! Procurement order can proceed.")
                st.balloons()

    with col2:
        if st.button("❌ Reject Recommendation", type="secondary", use_container_width=True):
            response = requests.post(
                "http://127.0.0.1:8000/api/approve",
                params={"approved": False}
            )
            if response.status_code == 200:
                st.error("❌ Recommendation Rejected. Please review vendors manually.")