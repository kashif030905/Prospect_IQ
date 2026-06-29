import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProspectIQState

llm    = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def web_search_agent(state: ProspectIQState) -> ProspectIQState:
    location = state['target_location']
    industry = state['target_industry']
    size     = state['company_size']
    persona  = state['target_persona']

    # Step 1: Generate search queries
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
    """

    queries_response = llm.invoke(query_prompt)
    time.sleep(1)

    raw_queries = queries_response.content.strip().split('\n')
    queries = [q.strip() for q in raw_queries if q.strip() and location.lower() in q.lower()]

    if len(queries) < 3:
        queries = [
            f"{industry} companies in {location} {size}",
            f"top {industry} firms in {location} site:linkedin.com",
            f"{industry} businesses {location} directory listing",
            f"{persona} {industry} company {location}",
            f"best {industry} companies headquartered in {location}",
        ]

    queries = queries[:5]

    # Step 2: Run ALL searches in parallel
    seen_urls   = set()
    raw_results = []

    def search_one(query):
        try:
            return tavily.search(
                query=query,
                max_results=4,
                search_depth="basic"
            )
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(search_one, q): q for q in queries}
        for future in as_completed(futures):
            result = future.result()
            if not result:
                continue
            for r in result.get('results', []):
                url = r.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    raw_results.append({
                        "title":   r.get('title', ''),
                        "url":     url,
                        "content": r.get('content', '')[:300],
                        "score":   r.get('score', 0)
                    })

    # Step 3: Format results for LLM
    formatted_results = ""
    for i, r in enumerate(raw_results, 1):
        formatted_results += f"""
Result {i}:
  Title   : {r['title']}
  URL     : {r['url']}
  Snippet : {r['content']}
  Score   : {r['score']}
---"""

    # Step 4: Extract real companies
    extraction_prompt = f"""
    You are a Web Research AI Agent with expertise in B2B company identification.

    TARGET CRITERIA:
    - Industry  : {industry}
    - Location  : {location} — STRICT, only include companies HERE
    - Size      : {size}
    - ICP       : {state['icp_profile'][:500]}

    RAW SEARCH RESULTS:
    {formatted_results}

    CRITICAL RULES:
    1. ONLY include companies clearly located in {location}
    2. REJECT any company NOT in {location}
    3. REJECT news articles, blogs, or directory pages — only real companies
    4. NEVER invent or hallucinate companies
    5. Use EXACT company name and URL from search result

    For each VERIFIED company found in {location}, provide EXACTLY this format:

    ============================================================
    COMPANY NAME    : [exact name]
    WEBSITE         : [exact URL]
    LOCATION        : [city, country]
    INDUSTRY        : [specific sub-industry]
    COMPANY SIZE    : [employee count if available]
    WHAT THEY DO    : [2 sentence description]
    WHY THEY MATCH  : [specific reasons they match our ICP]
    DATA SOURCE     : [search result title and URL]
    ============================================================

    End with:
    TOTAL COMPANIES FOUND IN {location}: [number]
    """

    response = llm.invoke(extraction_prompt)
    time.sleep(1)

    state["companies_found"] = response.content
    return state