from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProspectIQState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def icp_agent(state: ProspectIQState) -> ProspectIQState:
    """
    ICP Agent - Defines the Ideal Customer Profile.
    Creates a detailed, location-specific profile of the perfect customer.
    """
    prompt = f"""
    You are an Ideal Customer Profile (ICP) Specialist AI Agent with expertise in
    B2B SaaS markets across different geographies.

    User Inputs:
    - Product        : {state['product_description']}
    - Industry       : {state['target_industry']}
    - Company Size   : {state['company_size']}
    - Decision Maker : {state['target_persona']}
    - Location       : {state['target_location']}
    - Discovery Plan : {state['plan']}

    ⚠️ STRICT RULE: The ICP must be built EXCLUSIVELY for companies located in
    {state['target_location']}. Location is a HARD filter — any company outside
    {state['target_location']} is automatically disqualified.

    Define a comprehensive Ideal Customer Profile:

    ---
    SECTION 1 — COMPANY PROFILE
    - Industry        : {state['target_industry']}
    - Geography       : STRICTLY {state['target_location']} only
    - Company Size    : {state['company_size']}
    - Business Model  : (B2B / B2C / Both)
    - Growth Stage    : (Startup / SME / Enterprise)
    - Annual Revenue  : (estimated range for this size in {state['target_location']})

    SECTION 2 — PAIN POINTS
    List the top 3 specific problems our product solves for this ICP:
    - Pain Point 1:
    - Pain Point 2:
    - Pain Point 3:

    SECTION 3 — BUYING SIGNALS (triggers that indicate they need our product)
    - Signal 1:
    - Signal 2:
    - Signal 3:

    SECTION 4 — QUALIFICATION CRITERIA
    MUST HAVE (hard filters — company must meet ALL of these):
    - [ ] Located in {state['target_location']}
    - [ ] Industry: {state['target_industry']}
    - [ ] Size: {state['company_size']}
    - [ ] (add 2 more relevant must-haves)

    NICE TO HAVE (soft filters — bonus if they have these):
    - (list 3)

    DISQUALIFIERS (automatically skip if any of these are true):
    - Company is NOT located in {state['target_location']}
    - (list 2 more)

    SECTION 5 — LOCATION-SPECIFIC SEARCH QUERIES
    Generate 5 highly specific web search queries to find REAL companies in
    {state['target_location']} that match this ICP.
    Each query MUST include the location "{state['target_location']}" explicitly.
    Format: one query per line, no numbering, no bullet points.
    ---
    """

    response = llm.invoke(prompt)
    state["icp_profile"] = response.content
    return state