import streamlit as st

def render_results_section(results: dict):
    st.header("📊 Customer Discovery Results")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Companies Found",
        "✅ Validated Companies",
        "👤 Decision Makers",
        "📬 Enriched Contacts",
        "🎯 Recommendations"
    ])

    with tab1:
        st.markdown(results.get("companies_found", "No companies found yet"))

    with tab2:
        st.markdown(results.get("validated_companies", "No validated companies yet"))

    with tab3:
        st.markdown(results.get("decision_makers", "No decision makers found yet"))

    with tab4:
        st.markdown(results.get("enriched_contacts", "No enriched contacts yet"))

    with tab5:
        st.info(results.get("recommendations", "No recommendations yet"))