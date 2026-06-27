from langchain_groq import ChatGroq
from tavily import TavilyClient
from config.settings import GROQ_API_KEY, MODEL_NAME, TAVILY_API_KEY
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def contact_enrichment_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Contact Enrichment Agent - Enriches each decision maker with verified contact info.
    Searches web for emails, LinkedIn, recent activity, and personalization hooks.
    """
    location = state['target_location']
    industry = state['target_industry']
    persona = state['target_persona']

    # Step 1: Extract company + person pairs from decision maker output
    extract_prompt = f"""
    From the decision maker report below, extract a list of:
    COMPANY NAME | PERSON NAME (or "To be verified") | JOB TITLE

    Return one entry per line in this exact format:
    CompanyName | PersonName | JobTitle

    Decision Maker Report:
    {state['decision_makers']}
    """

    extract_response = llm.invoke(extract_prompt)
    contacts_raw = [
        line.strip() for line in extract_response.content.strip().split('\n')
        if '|' in line
    ][:3]

    all_enriched = ""

    for contact_line in contacts_raw:
        parts = [p.strip() for p in contact_line.split('|')]
        company = parts[0] if len(parts) > 0 else "Unknown"
        person = parts[1] if len(parts) > 1 else "To be verified"
        title = parts[2] if len(parts) > 2 else persona

        # Step 2: Search for real contact information
        search_results = ""
        search_queries = [
            f"{person} {company} {location} email contact",
            f"{person} {title} {company} LinkedIn",
            f"{company} {location} {title} contact details",
        ]

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

        # Step 3: Enrich contact with all found info
        enrich_prompt = f"""
        You are a Contact Intelligence AI Agent specialising in B2B outreach enrichment.

        Enrich the following contact using the search results provided.

        CONTACT TO ENRICH:
        - Name    : {person}
        - Title   : {title}
        - Company : {company}
        - Location: {location}

        SEARCH RESULTS:
        {search_results if search_results else "No direct results — use industry knowledge and reasonable inference."}

        ⚠️ RULES:
        - For email: if not found directly, infer from the company's known email pattern
          (e.g. if company uses firstname@company.com pattern, apply it)
        - Mark inferred data clearly as "(Inferred)" vs "(Verified)"
        - For LinkedIn: construct the most likely URL or say "Search manually"
        - NEVER fabricate specific personal details — be honest about confidence level

        Provide EXACTLY this format:

        ╔═════════════════════════════════════════════════════╗
        ║ CONTACT: {person} — {company}
        ╠═════════════════════════════════════════════════════╣
        ║ BASIC INFO
        ║   Full Name      : {person}
        ║   Job Title      : {title}
        ║   Company        : {company}
        ║   Location       : {location}
        ║
        ║ CONTACT DETAILS
        ║   Email          : [address or pattern] (Verified/Inferred)
        ║   LinkedIn       : [URL or "Search: name + company on LinkedIn"]
        ║   Phone          : [if found, else "Not publicly available"]
        ║   Twitter/X      : [handle if found, else "N/A"]
        ║
        ║ OUTREACH INTEL
        ║   Best Channel   : Email / LinkedIn / Phone
        ║   Best Time      : [day/time recommendation for {location} timezone]
        ║   Response Rate  : [estimated % based on role and channel]
        ║
        ║ PERSONALIZATION
        ║   Hook           : [one specific, researched thing to mention — recent
        ║                    news, company achievement, or role-specific pain]
        ║   Avoid          : [what NOT to say to this person]
        ║
        ║ EMAIL TEMPLATE
        ║   Subject Line   : [compelling, personalized subject]
        ║   Opening Line   : [personalized first sentence referencing their context]
        ║   Value Prop     : [2 sentences connecting product to their pain]
        ║   CTA            : [single, low-friction call to action]
        ╚═════════════════════════════════════════════════════╝
        """

        enrich_response = llm.invoke(enrich_prompt)
        all_enriched += f"\n\n{enrich_response.content}"

    # Step 4: Add overall outreach strategy
    strategy_prompt = f"""
    Based on these enriched contacts for {industry} companies in {location}:
    {all_enriched[:1000]}

    Write a concise OUTREACH STRATEGY OVERVIEW (8-10 lines) covering:
    1. Recommended contact sequence (who to reach first, second, third)
    2. Best overall channel mix for this industry and location
    3. Key message theme that will resonate across all contacts
    4. One risk to watch out for in this outreach campaign
    """

    strategy_response = llm.invoke(strategy_prompt)

    state["enriched_contacts"] = (
        all_enriched
        + "\n\n═══════════════════════════════════════\n"
        + "OUTREACH STRATEGY OVERVIEW\n"
        + "═══════════════════════════════════════\n"
        + strategy_response.content
    )
    return state