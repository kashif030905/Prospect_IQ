from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def comparison_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Vendor Comparison Agent.
    Reads extracted vendor data and creates a side by side comparison.
    """
    extracted_data = state["extracted_data"]
    vendor_names = state["vendor_names"]

    prompt = f"""
    You are a Vendor Comparison AI Agent specialized in procurement.
    
    Based on the following extracted vendor information, create a detailed 
    side by side comparison of all vendors.
    
    Vendors being compared: {', '.join(vendor_names)}
    
    Extracted Vendor Data:
    {extracted_data}
    
    Create a comparison that covers:
    1. Price comparison
    2. Payment terms comparison
    3. Delivery timeline comparison
    4. Warranty and support comparison
    5. Overall strengths and weaknesses of each vendor
    
    Present this as a clear, structured comparison table and summary.
    Be specific with numbers and terms where available.
    """

    response = llm.invoke(prompt)

    # Write comparison to shared state
    state["comparison"] = response.content

    return state