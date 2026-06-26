import streamlit as st

def render_results_section(results: dict):
    """
    Renders the analysis results from all agents.
    results: dictionary containing comparison, risks, negotiation, recommendation
    """
    st.header("📊 Procurement Analysis Results")

    # Vendor Comparison
    st.subheader("🔍 Vendor Comparison")
    st.markdown(results.get("comparison", "No comparison available"))
    st.divider()

    # Risk Analysis
    st.subheader("⚠️ Risk Analysis")
    st.markdown(results.get("risks", "No risk analysis available"))
    st.divider()

    # Negotiation Strategies
    st.subheader("🤝 Negotiation Strategies")
    st.markdown(results.get("negotiation", "No negotiation strategies available"))
    st.divider()

    # Final Recommendation
    st.subheader("✅ Final Recommendation")
    st.markdown(results.get("recommendation", "No recommendation available"))