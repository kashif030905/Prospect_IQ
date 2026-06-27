import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm    = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def decision_maker_agent(state: ProcureAIState) -> ProcureAIState:
    location = state['target_location']
    persona  = state['target_persona']

    # Step 1: Extract top 3 company names
    extract_prompt = f"""
    From the validated companies report below, extract ONLY the names of the
    TOP 3 SHORTLISTED companies (marked as #1, #2, #3 Priority or "Pursue Now").

    Return ONLY the company names, one per line, nothing else.
    No numbering, no bullets, no extra text.

    Validated Companies Report:
    {state['validated_companies']}
    """

    companies_response = llm.invoke(extract_prompt)
    time.sleep(1)

    company_names = [
        c.strip() for c in companies_response.content.strip().split('\n')
        if c.strip() and len(c.strip()) > 2
    ][:3]

    if not company_names:
        state["decision_makers"] = "Could not extract company names from validation report."
        return state

    # Step 2: Search and process each company
    def search_company(company):
        search_queries = [
            f"{persona} at {company} {location} LinkedIn",
            f"{company} {location} {persona} contact",
            f"site:linkedin.com {company} {persona} {location}",
        ]

        def run_search(query):
            try:
                return tavily.search(
                    query=query,
                    max_results=3,
                    search_depth="basic"
                )
            except Exception:
                return None

        search_results = ""
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(run_search, q): q for q in search_queries}
            for future in as_completed(futures):
                result = future.result()
                if not result:
                    continue
                for r in result.get('results', []):
                    search_results += f"\nTitle   : {r.get('title', '')}"
                    search_results += f"\nURL     : {r.get('url', '')}"
                    search_results += f"\nSnippet : {r.get('content', '')[:250]}"
                    search_results += "\n---"

        dm_prompt = f"""
        You are a Decision Maker Research AI Agent.

        Find the most relevant {persona} at {company} (located in {location}).

        SEARCH RESULTS:
        {search_results if search_results else "No direct results found."}

        RULES:
        - Only include people who work at {company}
        - If you cannot confirm a name, write "To be verified"
        - NEVER invent names
        - Use plain text format below — no box characters

        OUTPUT FORMAT:

        COMPANY: {company}
        Full Name      : [Name or "To be verified"]
        Confidence     : High / Medium / Low
        Job Title      : [Most likely title]
        Department     : [Department]
        Location       : [City, {location}]
        Seniority      : [C-Suite / VP / Director / Manager]
        WHY THIS PERSON: [1-2 sentences on why this person is the right contact]
        LinkedIn Search: [Exact string to search on LinkedIn]
        LinkedIn URL   : [https://linkedin.com/in/... if found, else "Search manually"]
        Google Search  : [Query to find their profile]
        Additional Context: [Any extra info from search results]
        """

        dm_response = llm.invoke(dm_prompt)
        time.sleep(1)
        return f"\n\nCOMPANY: {company}\n{dm_response.content}"

    # Run all companies sequentially to avoid rate limits
    all_decision_makers = ""
    for company in company_names:
        result = search_company(company)
        if result:
            all_decision_makers += result
        time.sleep(2)

    # Step 3: Outreach summary
    summary_prompt = f"""
    Based on these decision maker profiles:
    {all_decision_makers}

    Write a brief OUTREACH PRIORITY SUMMARY (5-7 lines) covering:
    1. Which decision maker to contact first and why
    2. Best channel for each (LinkedIn / Email / Phone)
    3. One personalization angle per person

    Keep it concise and actionable.
    """

    summary_response = llm.invoke(summary_prompt)
    time.sleep(1)

    state["decision_makers"] = (
        all_decision_makers
        + "\n\nOUTREACH PRIORITY SUMMARY\n"
        + "=" * 40 + "\n"
        + summary_response.content
    )
    return state