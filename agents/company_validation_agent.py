from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def company_validation_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Company Validation Agent - Validates and scores each company found.
    Checks if each company truly matches the ICP criteria.
    """
    prompt = f"""
    You are a Company Validation AI Agent specialized in B2B sales qualification.
    
    Your job is to validate each company found against our Ideal Customer Profile.
    
    ICP Profile:
    {state['icp_profile']}
    
    Companies Found:
    {state['companies_found']}
    
    For each company, provide:
    
    1. VALIDATION SCORE: (0-100)
    2. ICP MATCH: (Strong / Medium / Weak)
    3. QUALIFYING FACTORS: Why they match
    4. DISQUALIFYING FACTORS: Why they might not match
    5. RECOMMENDATION: (Pursue / Maybe / Skip)
    
    At the end, provide a SHORTLIST of top 3 companies to pursue.
    Be strict with qualification — quality over quantity.
    """

    response = llm.invoke(prompt)
    state["validated_companies"] = response.content
    return state