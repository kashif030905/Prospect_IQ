from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def decision_maker_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Decision Maker Agent - Finds the right person to contact at each shortlisted company.
    Uses location + company + role to run targeted searches.
    """
    location = state['target_location']
    persona = state['target_persona']

    # Step 1: Extract only the TOP 3 shortlisted company names cleanly
    extract_prompt = f"""
    From the validated companies report below, extract ONLY the names of the
    TOP 3 SHORTLISTED companies (the ones marked as #1, #2, #3 Priority or
    marked as "Pursue").

    Return ONLY the company names, one per line, nothing else.
    No numbering, no bullets, no extra text.

    Validated Companies Report:
    {state['validated_companies']}
    """

    companies_response = llm.invoke(extract_prompt)
    company_names = [
        c.strip() for c in companies_response.content.strip().split('\n')
        if c.strip() and len(c.strip()) > 2
    ][:3]

    all_decision_makers = ""

    for company in company_names:
        # Step 2: Search for the actual decision maker at this company
        search_queries = [
            f"{persona} at {company} {location} LinkedIn",
            f"{company} {location} {persona} contact",
            f"site:linkedin.com {company} {persona} {location}",
        ]

        search_results = ""
        for query in search_queries:
            try:
                results = tavily.search(
                    query=query,
                    max_results=3,
                    search_depth="advanced"
                )
                for r in results.get('results', []):
                    search_results += f"\nTitle   : {r.get('title', '')}"
                    search_results += f"\nURL     : {r.get('url', '')}"
                    search_results += f"\nSnippet : {r.get('content', '')[:250]}"
                    search_results += "\n---"
            except Exception:
                continue

        # Step 3: Extract decision maker from search results
        dm_prompt = f"""
        You are a Decision Maker Research AI Agent.

        Find the most relevant {persona} at {company} (located in {location}).

        SEARCH RESULTS:
        {search_results if search_results else "No direct results found — use reasoning based on company profile."}

        ⚠️ RULES:
        - Only include people who work at {company}
        - Only include people based in {location} or the company's known location
        - If you cannot find a specific name from search results, say "To be verified"
          but still provide the role, department, and LinkedIn search strategy
        - NEVER invent a person's name — if uncertain, say so

        Provide EXACTLY this format:

        ┌─────────────────────────────────────────────────────┐
        │ COMPANY: {company}
        ├─────────────────────────────────────────────────────┤
        │ DECISION MAKER PROFILE
        │
        │ Full Name      : [Name or "To be verified via LinkedIn"]
        │ Confidence     : High / Medium / Low
        │ Job Title      : [Most likely title]
        │ Department     : [Department]
        │ Location       : [City, {location}]
        │ Seniority      : [C-Suite / VP / Director / Manager]
        │
        │ WHY THIS PERSON:
        │ [Explain why this role/person is the right decision maker for our product]
        │
        │ HOW TO FIND THEM:
        │ LinkedIn Search : [Exact search string to use on LinkedIn]
        │ LinkedIn URL    : [https://linkedin.com/in/... if found, else "Search manually"]
        │ Google Search   : [Query to find their profile or contact]
        │
        │ ADDITIONAL CONTEXT:
        │ [Any relevant info from search results about this company or person]
        └─────────────────────────────────────────────────────┘
        """

        dm_response = llm.invoke(dm_prompt)
        all_decision_makers += f"\n\n{dm_response.content}"

    # Add a summary at the end
    summary_prompt = f"""
    Based on these decision maker profiles:
    {all_decision_makers}

    Write a brief OUTREACH PRIORITY SUMMARY (5-7 lines) that tells the sales team:
    1. Which decision maker to contact first and why
    2. The best channel for each (LinkedIn / Email / Phone)
    3. One key personalization angle for each person

    Keep it concise and actionable.
    """

    summary_response = llm.invoke(summary_prompt)

    state["decision_makers"] = (
        all_decision_makers
        + "\n\n═══════════════════════════════════════\n"
        + "OUTREACH PRIORITY SUMMARY\n"
        + "═══════════════════════════════════════\n"
        + summary_response.content
    )
    return state