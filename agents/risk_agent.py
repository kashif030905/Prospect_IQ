from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def risk_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Risk Analysis Agent.
    Reads extracted vendor data and identifies hidden risks.
    """
    extracted_data = state["extracted_data"]
    vendor_names = state["vendor_names"]

    prompt = f"""
    You are a Risk Analysis AI Agent specialized in procurement.
    
    Analyze the following vendor quotations and identify risks for each vendor.
    
    Vendors: {', '.join(vendor_names)}
    
    Extracted Vendor Data:
    {extracted_data}
    
    For each vendor identify:
    1. Financial risks (payment terms, hidden costs)
    2. Delivery risks (unrealistic timelines, no penalties for delays)
    3. Quality risks (no warranty, vague support terms)
    4. Legal risks (unfavorable clauses, no dispute resolution)
    5. Overall risk level: Low / Medium / High
    
    Be specific and practical in your risk assessment.
    """

    response = llm.invoke(prompt)
    state["risks"] = response.content
    return state