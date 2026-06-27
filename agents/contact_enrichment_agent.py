from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def contact_enrichment_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Contact Enrichment Agent - Enriches contact information.
    Finds email, phone, LinkedIn profile for each decision maker.
    """
    # Search for contact details for each decision maker
    enrich_prompt = f"""
    You are a Contact Enrichment AI Agent.
    
    Based on the following decision makers found:
    {state['decision_makers']}
    
    For each decision maker, provide enriched contact information:
    
    1. FULL NAME:
    2. JOB TITLE:
    3. COMPANY:
    4. EMAIL FORMAT: (e.g. firstname@company.com based on company email pattern)
    5. LINKEDIN URL: (suggested profile URL)
    6. PHONE: (if available, otherwise "Not publicly available")
    7. TWITTER/X: (if available)
    8. BEST CONTACT METHOD: (Email / LinkedIn / Phone)
    9. BEST TIME TO REACH: (based on their role and industry)
    10. PERSONALIZATION TIP: (one specific thing to mention when reaching out)
    
    Also search for any recent news or activity about each person
    that could be used for personalized outreach.
    
    Be realistic — if information is not available publicly, say so clearly.
    """

    # Search for additional contact details
    search_results = ""
    try:
        results = tavily.search(
            query=f"contact email {state['target_persona']} {state['target_industry']}",
            max_results=3,
            search_depth="basic"
        )
        for r in results.get('results', []):
            search_results += f"\n{r.get('content', '')[:200]}"
    except Exception:
        search_results = "No additional results found"

    full_prompt = f"""
    You are a Contact Enrichment AI Agent.
    
    Decision Makers to Enrich:
    {state['decision_makers']}
    
    Additional Context from Web:
    {search_results}
    
    For each decision maker provide:
    1. FULL NAME:
    2. JOB TITLE:
    3. COMPANY:
    4. EMAIL: (best guess based on company pattern)
    5. LINKEDIN: (suggested URL)
    6. BEST CONTACT METHOD:
    7. PERSONALIZATION TIP: (something specific to mention)
    8. SUGGESTED SUBJECT LINE: (for cold email outreach)
    
    Be practical and realistic.
    """

    response = llm.invoke(full_prompt)
    state["enriched_contacts"] = response.content
    return state