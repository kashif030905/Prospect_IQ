from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def planner_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Planner Agent - Orchestrates the entire customer discovery workflow.
    Reads user inputs and creates a detailed discovery strategy.
    """
    prompt = f"""
    You are a Strategic Sales Planning AI Agent.
    
    A SaaS company has provided the following information:
    
    Product Description: {state['product_description']}
    Target Industry: {state['target_industry']}
    Company Size: {state['company_size']}
    Target Persona: {state['target_persona']}
    
    Create a detailed customer discovery strategy that includes:
    1. Key characteristics of ideal customers
    2. Best web sources to find these companies
    3. Key qualification criteria to validate companies
    4. How to identify the right decision makers
    5. Best outreach approach for this persona
    6. Expected business outcomes
    
    Be specific, practical and actionable.
    """

    response = llm.invoke(prompt)
    state["plan"] = response.content
    return state