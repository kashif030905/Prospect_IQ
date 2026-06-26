from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def negotiation_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Negotiation Strategy Agent.
    Reads comparison and risk data and suggests negotiation tactics.
    """
    comparison = state["comparison"]
    risks = state["risks"]
    vendor_names = state["vendor_names"]

    prompt = f"""
    You are a Negotiation Strategy AI Agent specialized in procurement.
    
    Based on the vendor comparison and risk analysis below,
    suggest specific negotiation strategies for each vendor.
    
    Vendors: {', '.join(vendor_names)}
    
    Vendor Comparison:
    {comparison}
    
    Risk Analysis:
    {risks}
    
    For each vendor provide:
    1. Key negotiation points (what to push for)
    2. Leverage points (what advantages we have)
    3. Concessions we can offer
    4. Specific asks (discount percentage, better payment terms, etc.)
    5. Walk away conditions (when to reject this vendor)
    
    Be specific and actionable in your recommendations.
    """

    response = llm.invoke(prompt)
    state["negotiation"] = response.content
    return state