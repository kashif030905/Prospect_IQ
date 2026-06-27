from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from backend.services.pdf_service import generate_pdf_report
from agents.graph import discovery_graph

router = APIRouter()

class DiscoveryRequest(BaseModel):
    product_description: str
    target_industry: str
    target_company_size: str
    target_role: str
    target_location: Optional[str] = "Not specified"


@router.post("/analyze")
async def analyze(request: DiscoveryRequest):
    try:
        initial_state = {
            "product_description": request.product_description,
            "target_industry": request.target_industry,
            "company_size": request.target_company_size,
            "target_persona": request.target_role,
            "target_location": request.target_location or "Not specified",  # ✅ FIXED
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
            "plan": result.get("plan"),
            "icp_profile": result.get("icp_profile"),
            "companies_found": result.get("companies_found"),
            "validated_companies": result.get("validated_companies"),
            "decision_makers": result.get("decision_makers"),
            "enriched_contacts": result.get("enriched_contacts"),
            "recommendations": result.get("recommendations")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_recommendation(approved: bool):
    if approved:
        return {
            "status": "approved",
            "message": "Outreach plan approved. Sales team can proceed."
        }
    else:
        return {
            "status": "rejected",
            "message": "Outreach plan rejected. Please refine the search criteria."
        }


@router.post("/report")
async def download_report(request: DiscoveryRequest):
    try:
        initial_state = {
            "product_description": request.product_description,
            "target_industry": request.target_industry,
            "company_size": request.target_company_size,
            "target_persona": request.target_role,
            "target_location": request.target_location or "Not specified",  # ✅ FIXED
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

        # Merge input fields into result so pdf_service can access them
        pdf_data = dict(result)
        pdf_data["product_description"] = request.product_description
        pdf_data["target_industry"]      = request.target_industry
        pdf_data["target_location"]      = request.target_location or "Not specified"
        pdf_data["target_persona"]       = request.target_role
        pdf_data["company_size"]         = request.target_company_size

        pdf_bytes = generate_pdf_report(pdf_data, [request.target_industry])

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=procureai_discovery_report.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))