from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def web_search_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Web Search Agent - Searches the internet for matching companies.
    Uses Tavily to find real companies based on the ICP.
    """
    prompt_for_queries = f"""
    Based on this ICP profile:
    {state['icp_profile']}
    
    Generate 3 specific Google search queries to find companies that match this profile.
    Return ONLY the 3 search queries, one per line, nothing else.
    """

    # Ask LLM to generate search queries
    queries_response = llm.invoke(prompt_for_queries)
    queries = queries_response.content.strip().split('\n')
    queries = [q.strip() for q in queries if q.strip()][:3]

    # Search the web for each query
    all_results = ""
    for query in queries:
        try:
            results = tavily.search(
                query=query,
                max_results=3,
                search_depth="basic"
            )
            for r in results.get('results', []):
                all_results += f"\nCompany: {r.get('title', 'N/A')}"
                all_results += f"\nURL: {r.get('url', 'N/A')}"
                all_results += f"\nDescription: {r.get('content', 'N/A')[:200]}"
                all_results += "\n---"
        except Exception as e:
            all_results += f"\nSearch error for query '{query}': {str(e)}"

    # Ask LLM to summarize findings
    summary_prompt = f"""
    You are a Web Research AI Agent.
    
    Based on these web search results, identify and list potential companies
    that match our Ideal Customer Profile:
    
    ICP Profile:
    {state['icp_profile']}
    
    Search Results:
    {all_results}
    
    For each potential company found, provide:
    1. Company name
    2. Website
    3. Brief description
    4. Why they match the ICP
    
    List up to 5 most relevant companies.
    """

    response = llm.invoke(summary_prompt)
    state["companies_found"] = response.content
    return state