from typing import TypedDict, List, Optional

class ProcureAIState(TypedDict):
    """
    This is the shared memory of our entire agent system.
    Every agent reads from and writes to this state.
    Think of it as a shared Google Doc for all agents.
    """
    # Input data
    vendor_names: List[str]        # Names of vendors
    vendor_texts: List[str]        # Raw text extracted from PDFs

    # Agent outputs (each agent fills one of these)
    plan: Optional[str]            # Planner agent output
    extracted_data: Optional[str]  # Document agent output
    comparison: Optional[str]      # Comparison agent output
    risks: Optional[str]           # Risk agent output
    negotiation: Optional[str]     # Negotiation agent output
    recommendation: Optional[str]  # Recommendation agent output

    # Human in the loop
    human_approved: Optional[bool] # True if human approved the recommendation