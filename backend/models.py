from pydantic import BaseModel
from typing import List, Optional

# This model defines what data the frontend sends to the backend
# when requesting an analysis
class AnalysisRequest(BaseModel):
    vendor_texts: List[str]  # List of text extracted from each PDF
    vendor_names: List[str]  # List of vendor names

# This model defines what the backend sends back to the frontend
class AnalysisResponse(BaseModel):
    status: str                    # "success" or "error"
    comparison: Optional[str]      # Vendor comparison table
    risks: Optional[str]           # Risk analysis results
    negotiation: Optional[str]     # Negotiation strategies
    recommendation: Optional[str]  # Final recommendation
    message: Optional[str]         # Error message if something goes wrong