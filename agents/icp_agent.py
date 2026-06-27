from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def icp_agent(state: ProcureAIState) -> ProcureAIState:
    """
    ICP Agent - Defines the Ideal Customer Profile.
    Creates a detailed profile of the perfect customer based on user inputs.
    """
    prompt = f"""
    You are an Ideal Customer Profile (ICP) Specialist AI Agent.
    
    Based on the following information:
    Product Description: {state['product_description']}
    Target Industry: {state['target_industry']}
    Company Size: {state['company_size']}
    Target Persona: {state['target_persona']}
    Discovery Plan: {state['plan']}
    
    Define a detailed Ideal Customer Profile that includes:
    1. COMPANY PROFILE: Industry, size, location, business model, growth stage
    2. PAIN POINTS: Top 3 problems this product solves
    3. BUYING SIGNALS: Signs they need our product, triggers, events to watch
    4. QUALIFICATION CRITERIA: Must have, nice to have, disqualification criteria
    5. SEARCH KEYWORDS: Top 5 Google search queries to find these companies
    
    Be very specific and practical.
    """

    response = llm.invoke(prompt)
    state["icp_profile"] = response.content
    return state