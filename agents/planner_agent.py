from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def planner_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Planner Agent - Orchestrates the entire customer discovery workflow.
    Reads user inputs and creates a detailed, location-specific discovery strategy.
    """
    prompt = f"""
    You are a Strategic Sales Planning AI Agent with deep expertise in B2B SaaS sales.

    A SaaS company has provided the following information:

    Product Description : {state['product_description']}
    Target Industry     : {state['target_industry']}
    Company Size        : {state['company_size']}
    Target Persona      : {state['target_persona']}
    Target Location     : {state['target_location']}

    ⚠️ LOCATION IS CRITICAL: All strategies, searches, and recommendations MUST be
    strictly focused on companies based in or operating from: {state['target_location']}
    Do NOT suggest or include companies outside this location.

    Create a detailed, location-specific customer discovery strategy that includes:

    1. MARKET OVERVIEW
       - Size and maturity of the {state['target_industry']} market in {state['target_location']}
       - Key characteristics of companies in this region
       - Local business culture and buying behaviour

    2. IDEAL CUSTOMER CHARACTERISTICS
       - Firmographic profile (size, revenue, structure)
       - Technographic signals (tools they likely use)
       - Behavioural signals (events that trigger a purchase)

    3. SEARCH STRATEGY
       - Best platforms to find these companies in {state['target_location']}
         (e.g. LinkedIn, Tracxn, Crunchbase, local trade directories)
       - Top 5 location-specific search queries to use

    4. QUALIFICATION CRITERIA
       - Must-have criteria (hard filters)
       - Nice-to-have criteria (soft filters)
       - Automatic disqualifiers

    5. DECISION MAKER STRATEGY
       - How to identify the right {state['target_persona']} in {state['target_location']} companies
       - Common titles and org structures in this region

    6. OUTREACH APPROACH
       - Preferred communication channels in {state['target_location']}
       - Cultural considerations for outreach
       - Best times and formats for first contact

    Be specific, practical, and grounded in the realities of {state['target_location']} market.
    """

    response = llm.invoke(prompt)
    state["plan"] = response.content
    return state