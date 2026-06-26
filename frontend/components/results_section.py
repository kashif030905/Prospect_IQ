import streamlit as st

def render_results_section(results: dict):
    """
    Renders the analysis results in a professional tabbed layout.
    """
    st.header("📊 Procurement Analysis Results")

    # Show results in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Vendor Comparison",
        "⚠️ Risk Analysis",
        "🤝 Negotiation",
        "✅ Recommendation"
    ])

    with tab1:
        st.markdown(results.get("comparison", "No comparison available"))

    with tab2:
        st.markdown(results.get("risks", "No risk analysis available"))

    with tab3:
        st.markdown(results.get("negotiation", "No negotiation strategies available"))

    with tab4:
        # Highlight the recommendation
        st.info(results.get("recommendation", "No recommendation available"))