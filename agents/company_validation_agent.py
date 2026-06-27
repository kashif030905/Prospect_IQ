from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def company_validation_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Company Validation Agent - Deep validates and scores each company.
    Produces a professional comparison table with clear reasoning.
    Location is treated as a HARD disqualifier.
    """
    location = state['target_location']

    prompt = f"""
    You are a Senior B2B Sales Qualification AI Agent with expertise in pipeline quality.

    Your job: Rigorously validate each company against our ICP and produce a
    professional comparison report that helps the sales team make confident decisions.

    ═══════════════════════════════════════════════════════════
    QUALIFICATION CONTEXT
    ═══════════════════════════════════════════════════════════
    Product         : {state['product_description']}
    Target Location : {location} ← HARD FILTER
    ICP Profile     : {state['icp_profile']}

    COMPANIES TO VALIDATE:
    {state['companies_found']}

    ═══════════════════════════════════════════════════════════
    VALIDATION RULES (apply strictly)
    ═══════════════════════════════════════════════════════════
    RULE 1 — LOCATION IS A HARD DISQUALIFIER:
      If a company is NOT located in {location}, assign score 0 and mark DISQUALIFIED.
      Do not evaluate any other criteria for disqualified companies.

    RULE 2 — SCORING BREAKDOWN (100 points total):
      - Location match      : 30 points (0 if not in {location})
      - Industry fit        : 25 points
      - Company size match  : 20 points
      - Pain point fit      : 15 points
      - Growth signals      : 10 points

    RULE 3 — FINAL VERDICT:
      - 80-100 : 🟢 STRONG FIT  → Pursue immediately
      - 60-79  : 🟡 MEDIUM FIT  → Pursue with qualification call
      - 40-59  : 🟠 WEAK FIT    → Maybe, needs more research
      - 0-39   : 🔴 NO FIT      → Skip
      - 0 (disqualified) : ⛔ DISQUALIFIED → Not in {location}

    ═══════════════════════════════════════════════════════════
    OUTPUT FORMAT — produce this for EACH company:
    ═══════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────┐
    │ COMPANY: [Company Name]
    │ WEBSITE : [Exact URL]
    ├─────────────────────────────────────────────────────────┤
    │ SCORES
    │   Location Match     : __/30  [in {location}? Yes/No]
    │   Industry Fit       : __/25  [reasoning]
    │   Size Match         : __/20  [reasoning]
    │   Pain Point Fit     : __/15  [reasoning]
    │   Growth Signals     : __/10  [reasoning]
    │   ─────────────────────────────
    │   TOTAL SCORE        : __/100
    │   ICP MATCH          : 🟢 STRONG / 🟡 MEDIUM / 🟠 WEAK / 🔴 NO FIT / ⛔ DISQUALIFIED
    ├─────────────────────────────────────────────────────────┤
    │ WHY WE SHOULD PURSUE
    │   [3 specific, evidence-based reasons]
    │
    │ RISKS / CONCERNS
    │   [2 specific concerns or unknowns]
    │
    │ VERDICT: [Pursue Now / Qualify First / Skip / Disqualified]
    └─────────────────────────────────────────────────────────┘

    ═══════════════════════════════════════════════════════════
    COMPARISON SUMMARY TABLE
    ═══════════════════════════════════════════════════════════
    After validating all companies, produce this summary:

    | Rank | Company | Location ✓? | Score | ICP Match | Verdict |
    |------|---------|-------------|-------|-----------|---------|
    | 1    | ...     | Yes/No      | __/100| Strong    | Pursue  |
    (fill for all companies, sorted by score descending)

    ═══════════════════════════════════════════════════════════
    FINAL SHORTLIST — TOP 3 COMPANIES TO PURSUE
    ═══════════════════════════════════════════════════════════
    Based on the scores above, our recommended shortlist is:

    🥇 #1 PRIORITY: [Company Name]
       Why chosen over others: [specific comparative reasoning — what makes
       this company better than the others on the list]
       Confidence level: High / Medium / Low
       First action: [what to do immediately]

    🥈 #2 PRIORITY: [Company Name]
       Why chosen over others: [specific comparative reasoning]
       Confidence level: High / Medium / Low
       First action: [what to do immediately]

    🥉 #3 PRIORITY: [Company Name]
       Why chosen over others: [specific comparative reasoning]
       Confidence level: High / Medium / Low
       First action: [what to do immediately]

    WHY THIS ORDER:
    [Paragraph explaining the comparative logic — why #1 beats #2, why #2 beats #3,
    and what specific factors drove these rankings]
    """

    response = llm.invoke(prompt)
    state["validated_companies"] = response.content
    return state