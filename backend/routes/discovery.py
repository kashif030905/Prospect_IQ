from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from backend.services.pdf_service import generate_pdf_report
from agents.graph import discovery_graph

router = APIRouter()

class DiscoveryRequest(BaseModel):
    product_description: str
    target_industry: str
    company_size: str
    target_persona: str

@router.post("/analyze")
async def analyze(request: DiscoveryRequest):
    try:
        initial_state = {
            "product_description": request.product_description,
            "target_industry": request.target_industry,
            "company_size": request.company_size,
            "target_persona": request.target_persona,
            "plan": None,
            "icp_profile": None,
            "companies_found": None,
            "validated_companies": None,
            "decision_makers": None,
            "enriched_contacts": None,
            "recommendations": None,
            "human_approved": None
        }

        result = discovery_graph.invoke(initial_state)

        return {
            "status": "success",
            "plan": result["plan"],
            "icp_profile": result["icp_profile"],
            "companies_found": result["companies_found"],
            "validated_companies": result["validated_companies"],
            "decision_makers": result["decision_makers"],
            "enriched_contacts": result["enriched_contacts"],
            "recommendations": result["recommendations"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_recommendation(approved: bool):
    if approved:
        return {"status": "approved", "message": "Outreach plan approved. Sales team can proceed."}
    else:
        return {"status": "rejected", "message": "Outreach plan rejected. Please refine the search criteria."}


@router.post("/report")
async def download_report(request: DiscoveryRequest):
    try:
        initial_state = {
            "product_description": request.product_description,
            "target_industry": request.target_industry,
            "company_size": request.company_size,
            "target_persona": request.target_persona,
            "plan": None,
            "icp_profile": None,
            "companies_found": None,
            "validated_companies": None,
            "decision_makers": None,
            "enriched_contacts": None,
            "recommendations": None,
            "human_approved": None
        }

        result = discovery_graph.invoke(initial_state)
        pdf_bytes = generate_pdf_report(result, [request.target_industry])

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=discovery_report.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))