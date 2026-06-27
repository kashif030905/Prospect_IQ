from pydantic import BaseModel
from typing import Optional

class DiscoveryRequest(BaseModel):
    product_description: str
    target_industry: str
    company_size: str
    target_persona: str

class DiscoveryResponse(BaseModel):
    status: str
    plan: Optional[str]
    icp_profile: Optional[str]
    companies_found: Optional[str]
    validated_companies: Optional[str]
    decision_makers: Optional[str]
    enriched_contacts: Optional[str]
    recommendations: Optional[str]
    message: Optional[str]