from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from typing import List
from backend.services.pdf_service import extract_text_from_pdf, generate_pdf_report
from backend.models import AnalysisResponse
from agents.graph import procurement_graph

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_quotations(files: List[UploadFile] = File(...)):
    try:
        vendor_texts = []
        vendor_names = []

        for file in files:
            file_bytes = await file.read()
            text = extract_text_from_pdf(file_bytes)
            vendor_texts.append(text)
            vendor_names.append(file.filename.replace(".pdf", ""))

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
    if approved:
        return {"status": "approved", "message": "Procurement recommendation approved by human."}
    else:
        return {"status": "rejected", "message": "Procurement recommendation rejected by human."}


@router.post("/report-from-results")
async def download_report_from_results(payload: dict):
    """
    Generates PDF from already-computed results.
    No LLM calls needed — uses results from /analyze endpoint.
    """
    try:
        vendor_names = payload.get("vendor_names", [])
        results = payload.get("results", {})

        pdf_bytes = generate_pdf_report(results, vendor_names)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=procureai_report.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))