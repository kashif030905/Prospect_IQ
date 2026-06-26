from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from backend.services.pdf_service import extract_text_from_pdf
from backend.models import AnalysisResponse
from agents.graph import procurement_graph

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_quotations(files: List[UploadFile] = File(...)):
    """
    Receives uploaded PDF files from the frontend.
    Extracts text from each PDF.
    Runs the agent pipeline.
    Returns the full analysis.
    """
    try:
        vendor_texts = []
        vendor_names = []

        # Extract text from each uploaded PDF
        for file in files:
            file_bytes = await file.read()
            text = extract_text_from_pdf(file_bytes)
            vendor_texts.append(text)
            vendor_names.append(file.filename.replace(".pdf", ""))

        # Build the initial state for the agents
        initial_state = {
            "vendor_names": vendor_names,
            "vendor_texts": vendor_texts,
            "plan": None,
            "extracted_data": None,
            "comparison": None,
            "risks": None,
            "negotiation": None,
            "recommendation": None,
            "human_approved": None
        }

        # Run the agent pipeline
        result = procurement_graph.invoke(initial_state)

        return AnalysisResponse(
            status="success",
            comparison=result["comparison"],
            risks=result["risks"],
            negotiation=result["negotiation"],
            recommendation=result["recommendation"],
            message=f"Analysis complete for {len(files)} vendors"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_recommendation(approved: bool):
    """
    Human-in-the-loop endpoint.
    Frontend calls this when the user approves or rejects the recommendation.
    """
    if approved:
        return {"status": "approved", "message": "Procurement recommendation approved by human."}
    else:
        return {"status": "rejected", "message": "Procurement recommendation rejected by human."}