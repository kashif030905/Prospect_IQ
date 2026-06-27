import streamlit as st

def render_input_section():

    # Initialize reset counter
    if "reset_count" not in st.session_state:
        st.session_state["reset_count"] = 0

    col_title, col_reset = st.columns([5, 1])
    with col_title:
        st.header("🎯 Define Your Target")
        st.write("Tell us about your product and ideal customer profile.")
    with col_reset:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset", use_container_width=True):
            for key in ["results", "user_inputs", "agent_status"]:
                if key in st.session_state:
                    del st.session_state[key]
            # Increment counter to force widget reset
            st.session_state["reset_count"] += 1
            st.rerun()

    # Use reset_count as part of widget keys so they re-render blank
    r = st.session_state["reset_count"]

    product_description = st.text_area(
        "📦 What does your product do?",
        placeholder="e.g. We sell cloud-based project management software that helps software teams track tasks, manage sprints, and collaborate in real-time",
        height=100,
        key=f"product_{r}"
    )

    col1, col2 = st.columns(2)

    with col1:
        target_company_size = st.selectbox(
            "🏢 Target Company Size",
            ["1-10 employees", "10-50 employees", "50-200 employees",
             "200-500 employees", "500-1000 employees", "1000+ employees"],
            key=f"size_{r}"
        )

        target_industry = st.text_input(
            "🏭 Target Industry",
            placeholder="e.g. IT and Software, Healthcare, Retail",
            key=f"industry_{r}"
        )

    with col2:
        target_role = st.selectbox(
            "👤 Decision Maker Role",
            ["CEO", "CTO", "CFO", "HR Director", "VP Sales",
             "VP Engineering", "Operations Manager", "Procurement Manager"],
            key=f"role_{r}"
        )

        target_location = st.text_input(
            "📍 Target Location",
            placeholder="e.g. Mumbai, India",
            key=f"location_{r}"
        )

    if product_description and target_industry and target_location:
        st.success("✅ Profile complete — ready to find customers!")
        return {
            "product_description": product_description,
            "target_company_size": target_company_size,
            "target_role": target_role,
            "target_industry": target_industry,
            "target_location": target_location
        }

    return None