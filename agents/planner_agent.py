from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

# Initialize the LLM (Groq)
llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def planner_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Planner Agent - The manager of all agents.
    Reads the vendor names and creates an analysis plan.
    """
    vendor_names = state["vendor_names"]
    
    prompt = f"""
    You are a Procurement Planning AI Agent.
    
    You have received quotations from the following vendors:
    {', '.join(vendor_names)}
    
    Create a brief procurement analysis plan that includes:
    1. What information to extract from each quotation
    2. How to compare the vendors
    3. What risks to look for
    4. What negotiation strategies to consider
    5. How to make the final recommendation
    
    Keep the plan concise and professional.
    """
    
    response = llm.invoke(prompt)
    
    # Write the plan to shared state
    state["plan"] = response.content
    
    return state