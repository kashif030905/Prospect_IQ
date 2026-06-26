import fitz  # fitz is the import name for PyMuPDF library

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Takes a PDF file as bytes and returns all text from it as a string.
    
    file_bytes: the raw bytes of the uploaded PDF file
    returns: extracted text as a single string
    """
    # Open the PDF from bytes (not from a file path)
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    
    extracted_text = ""
    
    # Loop through every page in the PDF
    for page_number in range(len(pdf_document)):
        # Get the page
        page = pdf_document[page_number]
        # Extract text from the page and add to our result
        extracted_text += page.get_text()
    
    # Close the document to free memory
    pdf_document.close()
    
    return extracted_text