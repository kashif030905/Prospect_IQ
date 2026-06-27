from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def web_search_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Web Search Agent - Searches for real companies STRICTLY in the target location.
    Uses Tavily with location-enforced queries to find verified, accurate companies.
    """
    location = state['target_location']
    industry = state['target_industry']
    size = state['company_size']
    persona = state['target_persona']

    # Step 1: Generate location-strict search queries
    query_prompt = f"""
    Generate 5 highly specific web search queries to find REAL companies that match ALL of:
    - Industry  : {industry}
    - Location  : {location} (THIS IS MANDATORY — must be in every query)
    - Size      : {size}

    Rules:
    - EVERY query must explicitly contain "{location}"
    - Queries must target company directories, LinkedIn, or business listings
    - No generic queries — be very specific to the industry and location
    - Return ONLY the 5 queries, one per line, nothing else, no numbering

    Examples of good query format:
    "{industry} companies in {location} {size} employees"
    "top {industry} firms {location} site:linkedin.com"
    "{industry} businesses {location} directory"
    """

    queries_response = llm.invoke(query_prompt)
    raw_queries = queries_response.content.strip().split('\n')
    queries = [q.strip() for q in raw_queries if q.strip() and location.lower() in q.lower()]

    # Fallback: if LLM didn't include location in queries, force it
    if len(queries) < 3:
        queries = [
            f"{industry} companies in {location} {size}",
            f"top {industry} firms in {location} site:linkedin.com",
            f"{industry} businesses {location} directory listing",
            f"{persona} {industry} company {location}",
            f"best {industry} companies headquartered in {location}",
        ]

    queries = queries[:5]

    # Step 2: Execute searches and collect VERIFIED raw results
    raw_results = []
    seen_urls = set()

    for query in queries:
        try:
            results = tavily.search(
                query=query,
                max_results=4,
                search_depth="advanced"  # upgraded from basic to advanced
            )
            for r in results.get('results', []):
                url = r.get('url', '')
                # Deduplicate by URL
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    raw_results.append({
                        "title": r.get('title', ''),
                        "url": url,
                        "content": r.get('content', '')[:300],
                        "score": r.get('score', 0)
                    })
        except Exception as e:
            continue

    # Step 3: Format raw results for LLM
    formatted_results = ""
    for i, r in enumerate(raw_results, 1):
        formatted_results += f"""
Result {i}:
  Title   : {r['title']}
  URL     : {r['url']}
  Snippet : {r['content']}
  Score   : {r['score']}
---"""

    # Step 4: Ask LLM to extract ONLY real, verified companies strictly from target location
    extraction_prompt = f"""
    You are a Web Research AI Agent with expertise in B2B company identification.

    TARGET CRITERIA:
    - Industry  : {industry}
    - Location  : {location} ← STRICT — only include companies HERE
    - Size      : {size}
    - ICP       : {state['icp_profile'][:500]}

    RAW SEARCH RESULTS:
    {formatted_results}

    ⚠️ CRITICAL RULES:
    1. ONLY include companies that are CLEARLY located in {location}
    2. REJECT any company that is NOT in {location} — even if it is a great fit otherwise
    3. REJECT any result that is a news article, blog, or directory page — only real companies
    4. NEVER invent or hallucinate companies — only use what is in the search results above
    5. Use the EXACT company name and URL from the search result — do not modify them
    6. If fewer than 3 real companies are found in {location}, say so honestly

    For each VERIFIED company found in {location}, provide EXACTLY this format:

    ============================================================
    COMPANY NAME    : [exact name from search result]
    WEBSITE         : [exact URL from search result — do not guess or modify]
    LOCATION        : [city, country — must be in {location}]
    INDUSTRY        : [specific sub-industry]
    COMPANY SIZE    : [employee count or range if available]
    WHAT THEY DO    : [2 sentence description from search snippet]
    WHY THEY MATCH  : [specific reasons they match our ICP]
    DATA SOURCE     : [the search result title and URL this came from]
    ============================================================

    End with:
    TOTAL COMPANIES FOUND IN {location}: [number]
    """

    response = llm.invoke(extraction_prompt)
    state["companies_found"] = response.content
    return state