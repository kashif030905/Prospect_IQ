from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def document_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Document Intelligence Agent.
    Reads raw PDF text and extracts key information from each vendor.
    """
    vendor_names = state["vendor_names"]
    vendor_texts = state["vendor_texts"]
    
    all_extracted = ""

    # Loop through each vendor and extract information
    for i, (name, text) in enumerate(zip(vendor_names, vendor_texts)):
        prompt = f"""
        You are a Document Intelligence AI Agent specialized in procurement.
        
        Extract the following information from this vendor quotation:
        - Vendor Name
        - Total Price / Cost
        - Payment Terms
        - Delivery Timeline
        - Warranty / Support Terms
        - Special Conditions or Clauses
        
        Vendor: {name}
        Quotation Text:
        {text}
        
        Present the extracted information in a clear, structured format.
        If any information is missing, write "Not specified".
        """
        
        response = llm.invoke(prompt)
        all_extracted += f"\n\n--- {name} ---\n{response.content}"
    
    # Write extracted data to shared state
    state["extracted_data"] = all_extracted
    
    return state