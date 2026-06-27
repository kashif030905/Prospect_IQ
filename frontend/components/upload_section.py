import streamlit as st

def render_input_section():
    st.header("🎯 Define Your Target")
    st.write("Tell us about your product and ideal customer profile.")

    product_description = st.text_area(
        "📦 What does your product do?",
        placeholder="e.g. We sell HR management software that automates payroll and attendance tracking",
        height=100
    )

    col1, col2 = st.columns(2)

    with col1:
        target_company_size = st.selectbox(
            "🏢 Target Company Size",
            ["1-10 employees", "10-50 employees", "50-200 employees", 
             "200-500 employees", "500-1000 employees", "1000+ employees"]
        )

        target_industry = st.text_input(
            "🏭 Target Industry",
            placeholder="e.g. Manufacturing, Healthcare, Retail"
        )

    with col2:
        target_role = st.selectbox(
            "👤 Decision Maker Role",
            ["CEO", "CTO", "CFO", "HR Director", "VP Sales", 
             "VP Engineering", "Operations Manager", "Procurement Manager"]
        )

        target_location = st.text_input(
            "📍 Target Location",
            placeholder="e.g. India, Mumbai, Bangalore"
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