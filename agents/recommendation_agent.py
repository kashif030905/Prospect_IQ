from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def recommendation_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Recommendation Agent - Creates final actionable recommendations.
    Reads all previous agent outputs and suggests next actions.
    """
    prompt = f"""
    You are a Chief Sales Strategy AI Agent.
    
    Based on the complete customer discovery analysis below,
    provide final actionable recommendations for the sales team.
    
    PRODUCT: {state['product_description']}
    TARGET PERSONA: {state['target_persona']}
    
    ICP PROFILE:
    {state['icp_profile']}
    
    VALIDATED COMPANIES:
    {state['validated_companies']}
    
    DECISION MAKERS:
    {state['decision_makers']}
    
    ENRICHED CONTACTS:
    {state['enriched_contacts']}
    
    Provide:
    
    1. TOP PROSPECT: (single best company to contact first and why)
    
    2. PRIORITIZED OUTREACH LIST:
       - Rank all companies from highest to lowest priority
       - Include contact name and recommended approach for each
    
    3. OUTREACH SEQUENCE:
       - Day 1: (action)
       - Day 3: (action)
       - Day 7: (action)
       - Day 14: (action)
    
    4. EMAIL TEMPLATE:
       - Subject line
       - Opening line (personalized)
       - Value proposition (2 sentences)
       - Call to action
    
    5. EXPECTED OUTCOMES:
       - Estimated response rate
       - Expected meetings from this list
       - Potential pipeline value
    
    6. NEXT STEPS:
       - Immediate actions for the sales team
    
    Be specific, actionable, and realistic.
    """

    response = llm.invoke(prompt)
    state["recommendations"] = response.content
    return state