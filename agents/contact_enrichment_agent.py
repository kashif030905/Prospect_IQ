import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm    = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def contact_enrichment_agent(state: ProcureAIState) -> ProcureAIState:
    location = state['target_location']
    industry = state['target_industry']
    persona  = state['target_persona']

    # Step 1: Extract contacts
    extract_prompt = f"""
    From the decision maker report below, extract a list of:
    COMPANY NAME | PERSON NAME (or "To be verified") | JOB TITLE

    Return one entry per line in this exact format:
    CompanyName | PersonName | JobTitle

    Decision Maker Report:
    {state['decision_makers']}
    """

    extract_response = llm.invoke(extract_prompt)
    time.sleep(1)

    contacts_raw = [
        line.strip() for line in extract_response.content.strip().split('\n')
        if '|' in line
    ][:3]

    # Step 2: Enrich each contact sequentially to avoid rate limits
    def enrich_contact(contact_line):
        parts   = [p.strip() for p in contact_line.split('|')]
        company = parts[0] if len(parts) > 0 else "Unknown"
        person  = parts[1] if len(parts) > 1 else "To be verified"
        title   = parts[2] if len(parts) > 2 else persona

        search_queries = [
            f"{person} {company} {location} email contact",
            f"{person} {title} {company} LinkedIn",
            f"{company} {location} {title} contact details",
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

        enrich_prompt = f"""
        You are a Contact Intelligence AI Agent specialising in B2B outreach enrichment.

        Enrich the following contact using the search results provided.

        CONTACT TO ENRICH:
        - Name    : {person}
        - Title   : {title}
        - Company : {company}
        - Location: {location}

        SEARCH RESULTS:
        {search_results if search_results else "No direct results found."}

        RULES:
        - For email: if not found, infer from company email pattern and mark as (Inferred)
        - Mark verified data as (Verified)
        - NEVER fabricate specific personal details
        - Use plain text format — no box characters

        OUTPUT FORMAT:

        CONTACT: {person} — {company}
        Full Name      : {person}
        Job Title      : {title}
        Company        : {company}
        Location       : {location}
        Email          : [address or pattern] (Verified/Inferred)
        LinkedIn       : [URL or "Search manually"]
        Phone          : [if found, else "Not publicly available"]
        Best Channel   : Email / LinkedIn / Phone
        Best Time      : [day/time recommendation for {location} timezone]
        Hook           : [one specific researched thing to mention]
        Avoid          : [what NOT to say to this person]
        Subject Line   : [compelling personalized subject]
        Opening Line   : [personalized first sentence]
        Value Prop     : [2 sentences connecting product to their pain]
        CTA            : [single low-friction call to action]
        """

        enrich_response = llm.invoke(enrich_prompt)
        time.sleep(1)
        return f"\n\n{enrich_response.content}"

    all_enriched = ""
    for contact in contacts_raw:
        result = enrich_contact(contact)
        if result:
            all_enriched += result
        time.sleep(2)

    # Step 3: Outreach strategy
    strategy_prompt = f"""
    Based on these enriched contacts for {industry} companies in {location}:
    {all_enriched[:1000]}

    Write a concise OUTREACH STRATEGY OVERVIEW (8-10 lines) covering:
    1. Recommended contact sequence
    2. Best overall channel mix for this industry and location
    3. Key message theme that will resonate across all contacts
    4. One risk to watch out for in this outreach campaign
    """

    strategy_response = llm.invoke(strategy_prompt)
    time.sleep(1)

    state["enriched_contacts"] = (
        all_enriched
        + "\n\nOUTREACH STRATEGY OVERVIEW\n"
        + "=" * 40 + "\n"
        + strategy_response.content
    )
    return state