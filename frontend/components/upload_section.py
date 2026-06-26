import streamlit as st

def render_upload_section():
    """
    Renders the PDF upload section.
    Returns a list of uploaded files or None.
    """
    st.header("📤 Upload Vendor Quotations")
    st.write("Upload PDF quotations from multiple vendors to begin analysis.")

    uploaded_files = st.file_uploader(
        "Upload Quotation PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="You can upload 2 or more vendor quotation PDFs"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        for file in uploaded_files:
            st.write(f"📄 {file.name}")

    return uploaded_files