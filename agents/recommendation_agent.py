from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def recommendation_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Recommendation Agent.
    Reads all previous agent outputs and makes a final vendor recommendation.
    """
    vendor_names = state["vendor_names"]
    comparison = state["comparison"]
    risks = state["risks"]
    negotiation = state["negotiation"]

    prompt = f"""
    You are a Chief Procurement AI Agent.
    
    Based on the complete analysis below, make a final vendor recommendation.
    
    Vendors evaluated: {', '.join(vendor_names)}
    
    Vendor Comparison:
    {comparison}
    
    Risk Analysis:
    {risks}
    
    Negotiation Strategies:
    {negotiation}
    
    Provide:
    1. RECOMMENDED VENDOR: (single best choice with clear reasoning)
    2. WHY THIS VENDOR: (top 3 reasons)
    3. CONDITIONS: (what terms to negotiate before signing)
    4. ALTERNATIVE: (second best option if first choice falls through)
    5. FINAL SUMMARY: (2-3 sentence executive summary for the procurement manager)
    
    Be decisive and clear in your recommendation.
    """

    response = llm.invoke(prompt)
    state["recommendation"] = response.content
    return state