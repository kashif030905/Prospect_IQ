from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from backend.services.pdf_service import extract_text_from_pdf
from backend.models import AnalysisResponse

# APIRouter is like a mini FastAPI app for just this file
router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_quotations(files: List[UploadFile] = File(...)):
    """
    Receives uploaded PDF files from the frontend.
    Extracts text from each PDF.
    Returns a basic response for now (agents come later).
    """
    try:
        vendor_texts = []
        vendor_names = []

        # Loop through each uploaded file
        for file in files:
            # Read the file bytes
            file_bytes = await file.read()
            # Extract text from PDF
            text = extract_text_from_pdf(file_bytes)
            vendor_texts.append(text)
            # Use the filename as vendor name for now
            vendor_names.append(file.filename.replace(".pdf", ""))

        return AnalysisResponse(
            status="success",
            comparison=f"Received {len(files)} vendor quotations",
            risks=None,
            negotiation=None,
            recommendation=None,
            message=f"Successfully extracted text from {len(files)} PDFs"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))