from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Any
from backend.services.pdf_service import generate_pdf_report
from backend.database import save_session, get_all_sessions, get_session_by_id, update_session_status
from agents.graph import discovery_graph

router = APIRouter()


class DiscoveryRequest(BaseModel):
    product_description: str
    target_industry: str
    target_company_size: str
    target_role: str
    target_location: Optional[str] = "Not specified"


class ReportRequest(DiscoveryRequest):
    results: Optional[dict[str, Any]] = None


@router.post("/analyze")
async def analyze(request: DiscoveryRequest):
    try:
        initial_state = {
            "product_description": request.product_description,
            "target_industry":     request.target_industry,
            "company_size":        request.target_company_size,
            "target_persona":      request.target_role,
            "target_location":     request.target_location or "Not specified",
            "plan":                None,
            "icp_profile":         None,
            "companies_found":     None,
            "validated_companies": None,
            "decision_makers":     None,
            "enriched_contacts":   None,
            "recommendations":     None,
            "human_approved":      None
        }

        result = discovery_graph.invoke(initial_state)

        # Save to database
        session_id = save_session(
            inputs  = request.dict(),
            results = result
        )

        return {
            "status":               "success",
            "session_id":           session_id,
            "plan":                 result.get("plan"),
            "icp_profile":          result.get("icp_profile"),
            "companies_found":      result.get("companies_found"),
            "validated_companies":  result.get("validated_companies"),
            "decision_makers":      result.get("decision_makers"),
            "enriched_contacts":    result.get("enriched_contacts"),
            "recommendations":      result.get("recommendations"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_recommendation(approved: bool, session_id: Optional[str] = None):
    status = "approved" if approved else "rejected"

    if session_id:
        update_session_status(session_id, status)

    if approved:
        return {
            "status":  "approved",
            "message": "Outreach plan approved. Sales team can proceed."
        }
    else:
        return {
            "status":  "rejected",
            "message": "Outreach plan rejected. Please refine the search criteria."
        }


@router.get("/sessions")
async def list_sessions():
    try:
        sessions = get_all_sessions()
        return {"status": "success", "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        session = get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "success", "session": session}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def download_report(request: ReportRequest):
    try:
        if request.results:
            result = request.results
        else:
            initial_state = {
                "product_description": request.product_description,
                "target_industry":     request.target_industry,
                "company_size":        request.target_company_size,
                "target_persona":      request.target_role,
                "target_location":     request.target_location or "Not specified",
                "plan":                None,
                "icp_profile":         None,
                "companies_found":     None,
                "validated_companies": None,
                "decision_makers":     None,
                "enriched_contacts":   None,
                "recommendations":     None,
                "human_approved":      None
            }
            result = discovery_graph.invoke(initial_state)

        pdf_data                      = dict(result)
        pdf_data["product_description"] = request.product_description
        pdf_data["target_industry"]   = request.target_industry
        pdf_data["target_location"]   = request.target_location or "Not specified"
        pdf_data["target_persona"]    = request.target_role
        pdf_data["company_size"]      = request.target_company_size

        pdf_bytes = generate_pdf_report(pdf_data, [request.target_industry])

        return Response(
            content     = pdf_bytes,
            media_type  = "application/pdf",
            headers     = {
                "Content-Disposition": "attachment; filename=prospectiq_report.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))