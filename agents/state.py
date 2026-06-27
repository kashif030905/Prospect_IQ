from typing import TypedDict, List, Optional

class ProcureAIState(TypedDict):
    """
    Shared memory for the Customer Discovery Agent Pipeline.
    Every agent reads from and writes to this state.
    """
    # User inputs
    product_description: str        # What the SaaS product does
    target_industry: str            # Which industry to target
    company_size: str               # Target company size
    target_persona: str             # Who to contact (CEO, CTO etc.)

    # Agent outputs
    plan: Optional[str]             # Planner Agent output
    icp_profile: Optional[str]      # ICP Agent output
    companies_found: Optional[str]  # Web Search Agent output
    validated_companies: Optional[str]  # Validation Agent output
    decision_makers: Optional[str]  # Decision Maker Agent output
    enriched_contacts: Optional[str]  # Contact Enrichment Agent output
    recommendations: Optional[str]  # Recommendation Agent output

    # Human in the loop
    human_approved: Optional[bool]