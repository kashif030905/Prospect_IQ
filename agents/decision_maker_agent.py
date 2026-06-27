from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def decision_maker_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Decision Maker Agent - Finds the right person to contact at each company.
    Searches for decision makers based on target persona.
    """
    # Extract company names from validated companies
    extract_prompt = f"""
    From the following validated companies list, extract ONLY the company names.
    Return them as a simple list, one per line, nothing else.
    
    {state['validated_companies']}
    """
    
    companies_response = llm.invoke(extract_prompt)
    company_names = [c.strip() for c in companies_response.content.strip().split('\n') if c.strip()][:3]

    all_decision_makers = ""

    for company in company_names:
        # Search for decision makers at this company
        search_query = f"{company} {state['target_persona']} LinkedIn"
        
        try:
            results = tavily.search(
                query=search_query,
                max_results=2,
                search_depth="basic"
            )
            
            search_results = ""
            for r in results.get('results', []):
                search_results += f"\n{r.get('title', '')}: {r.get('content', '')[:200]}"

        except Exception:
            search_results = "No results found"

        # Ask LLM to identify decision makers
        dm_prompt = f"""
        You are a Decision Maker Research AI Agent.
        
        Find the most relevant decision maker at {company} 
        for our target persona: {state['target_persona']}
        
        Search Results:
        {search_results}
        
        Provide:
        1. FULL NAME: (if found, otherwise "To be researched")
        2. JOB TITLE: 
        3. DEPARTMENT:
        4. WHY THIS PERSON: Why they are the right contact
        5. LINKEDIN SEARCH: Suggested LinkedIn search to find them
        """

        dm_response = llm.invoke(dm_prompt)
        all_decision_makers += f"\n\n=== {company} ===\n{dm_response.content}"

    state["decision_makers"] = all_decision_makers
    return state