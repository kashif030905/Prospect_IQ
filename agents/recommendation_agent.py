import re
from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProspectIQState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

_SKIP = {"VALIDATION", "REPORT", "CONTEXT", "RULE", "OUTPUT", "SCORES", "COMPANY"}


def _extract_company_names(validated_text: str, companies_found: str) -> list[str]:
    names: list[str] = []
    for text in (validated_text or "", companies_found or ""):
        if not text.strip():
            continue
        for pattern in (r"COMPANY\s*:\s*(.+)", r"COMPANY NAME\s*:\s*(.+)"):
            for m in re.finditer(pattern, text, re.I):
                name = re.sub(r"[│┌╔#*|]", "", m.group(1)).strip()
                if (
                    name
                    and len(name) > 2
                    and name.upper() not in _SKIP
                    and not any(x in name.upper() for x in _SKIP)
                    and name not in names
                ):
                    names.append(name)
        if names:
            break
    return names


def _extract_scores_map(validated_text: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    if not validated_text:
        return scores
    for block in re.split(r"COMPANY\s*\d*\s*:", validated_text, flags=re.I):
        block = block.strip()
        if len(block) < 10:
            continue
        name = re.sub(r"[│┌╔#*|]", "", block.split("\n")[0]).strip()
        if not name or len(name) < 2:
            continue
        for pat in (
            r"TOTAL SCORE\s*:\s*(\d+)\s*/\s*100",
            r"TOTAL SCORE\s*:\s*(\d+)",
        ):
            m = re.search(pat, block, re.I)
            if m:
                scores[name.lower()] = min(int(m.group(1)), 100)
                break
        if name.lower() not in scores:
            parts = re.findall(
                r"(?:Location Match|Industry Fit|Size Match|Pain Point Fit|Growth Signals)\s*:\s*(\d+)\s*/",
                block, re.I,
            )
            if parts:
                scores[name.lower()] = min(sum(int(p) for p in parts), 100)
    return scores


def _table_rows(names: list[str], scores: dict[str, int]) -> str:
    medals = ["1st", "2nd", "3rd"]
    rows = []
    for i, name in enumerate(names):
        medal = medals[i] if i < len(medals) else f"{i + 1}th"
        score = scores.get(name.lower(), scores.get(name, 0))
        rows.append(f"| {medal} | {name} | {score}/100 | [contact] | [channel] | [reason] |")
    return "\n".join(rows)


def recommendation_agent(state: ProspectIQState) -> ProspectIQState:
    """
    Recommendation Agent - Synthesises all agent outputs into a final,
    actionable sales playbook. This is the board-level summary.
    """
    company_names = _extract_company_names(
        state.get("validated_companies", ""),
        state.get("companies_found", ""),
    )
    scores_map = _extract_scores_map(state.get("validated_companies", ""))
    n = len(company_names)
    names_list = "\n".join(f"  - {name}" for name in company_names) if company_names else "  (none found)"
    scores_list = "\n".join(
        f"  - {name}: {scores_map.get(name.lower(), 'N/A')}/100"
        for name in company_names
    ) if company_names else "  (none)"

    if n == 0:
        table_section = """
    ## PRIORITISED PROSPECT LIST

    No validated companies were found in this discovery session.
    State clearly that no prospects are available and recommend refining search criteria.
    Do NOT invent placeholder companies.
        """
        template_b = ""
        prospect_count = 0
    elif n == 1:
        sc = scores_map.get(company_names[0].lower(), "N/A")
        table_section = f"""
    ## PRIORITISED PROSPECT LIST

    ONLY 1 company was found. Include EXACTLY 1 row.

    | Priority | Company | Score | Contact | Best Channel | Why This Rank |
    |----------|---------|-------|---------|--------------|---------------|
    | 1st | {company_names[0]} | {sc}/100 | [contact name & title] | [channel] | [reason] |
        """
        template_b = ""
        prospect_count = 1
    else:
        table_section = f"""
    ## PRIORITISED PROSPECT LIST

    EXACTLY {n} companies were found. Include EXACTLY {n} rows using these scores:

    VALIDATED SCORES (use exactly — do NOT write "awaiting", "?", or "/100"):
{scores_list}

    | Priority | Company | Score | Contact | Best Channel | Why This Rank |
    |----------|---------|-------|---------|--------------|---------------|
{_table_rows(company_names, scores_map)}
        """
        template_b = """
    ### Template B — For Other Prospects (semi-personalized)
    Subject : [Subject line]
    Body    :
    Hi [Name],

    [Opening line]

    [Value prop]

    [CTA]

    Best,
    [Your Name]
        """
        prospect_count = n

    prompt = f"""
    You are the Chief Revenue Officer (CRO) AI Agent for ProspectIQ.

    You have received the full customer discovery analysis from 6 specialised agents.
    Your job: synthesise everything into a crisp, professional sales playbook that
    a sales team can execute starting TODAY.

    CRITICAL RULE: You may ONLY reference companies from this verified list:
{names_list}

    NEVER invent, guess, or use placeholder company names (e.g. "Company B", "Company C",
    "Prospect 2", "TBD"). If only {n} compan{"y" if n == 1 else "ies"} {"was" if n == 1 else "were"} found,
    your output must reflect exactly {n} — not 3.

    VALIDATED SCORES — copy these exact numbers into every Score field:
{scores_list}

    NEVER write "?", "/100", "awaiting score", or "N/A" for scores. Use the numbers above.

    ═══════════════════════════════════════════════════════════
    FULL DISCOVERY CONTEXT
    ═══════════════════════════════════════════════════════════
    PRODUCT         : {state['product_description']}
    TARGET PERSONA  : {state['target_persona']}
    TARGET LOCATION : {state['target_location']}
    TARGET INDUSTRY : {state['target_industry']}
    COMPANIES FOUND : {n}

    ICP PROFILE:
    {state['icp_profile'][:600]}

    VALIDATED COMPANIES (with scores):
    {state['validated_companies'][:800]}

    DECISION MAKERS:
    {state['decision_makers'][:600]}

    ENRICHED CONTACTS:
    {state['enriched_contacts'][:600]}

    ═══════════════════════════════════════════════════════════
    OUTPUT — PROFESSIONAL SALES PLAYBOOK
    ═══════════════════════════════════════════════════════════

    ## EXECUTIVE SUMMARY
    [3-4 sentences: state exactly {n} compan{"y" if n == 1 else "ies"} found, top recommendation, expected outcome]

    ---

    ## TOP PROSPECT — IMMEDIATE ACTION
    Company   : [Name from verified list only]
    Why #1    : [Specific reasoning — what makes this the BEST opportunity]
    Score     : [exact number from validated scores above]/100
    Contact   : [Name, Title]
    Action    : [Exactly what to do in the next 24 hours]

    ---
{table_section}

    WHY THIS RANKING:
    [Paragraph explaining the ranking using the validated scores above]

    ---

    ## 14-DAY OUTREACH SEQUENCE

    Day 1  — [Specific action: who to contact, which channel, what to say]
    Day 2  — [Follow-up or next prospect action]
    Day 3  — [Action]
    Day 5  — [Action]
    Day 7  — [Action]
    Day 10 — [Action]
    Day 14 — [Final follow-up or pivot decision]

    ---

    ## PROVEN EMAIL TEMPLATES

    ### Template A — For Top Prospect (personalized)
    Subject : [Subject line]
    Body    :
    Hi [Name],

    [Opening line — personalized reference]

    [Pain point sentence — their specific problem]

    [Value prop — how our product solves it in 1-2 sentences]

    [CTA — single, low friction ask]

    Best,
    [Your Name]

    ---
{template_b}
    ---

    ## EXPECTED OUTCOMES

    | Metric                  | Estimate         | Basis                    |
    |-------------------------|------------------|--------------------------|
    | Emails sent             | [n]              | {prospect_count} prospect{"s" if prospect_count != 1 else ""} × sequence |
    | Expected open rate      | [%]              | Industry avg for location|
    | Expected reply rate     | [%]              | Role + channel mix       |
    | Expected meetings booked| [n]              | Reply rate × conversion  |
    | Pipeline value (est.)   | ₹[amount]        | Deal size × meetings     |
    | Time to first response  | [X-Y days]       | Typical for this persona |

    ---

    ## IMMEDIATE NEXT STEPS

    ✅ Step 1: [Action — be specific, include who does what]
    ✅ Step 2: [Action]
    ✅ Step 3: [Action]
    ✅ Step 4: [Action]
    ✅ Step 5: [Action]

    ---

    ## RISKS & MITIGATION

    | Risk                    | Likelihood | Impact | Mitigation              |
    |-------------------------|------------|--------|-------------------------|
    | [Risk 1]                | High/Med/Low| H/M/L | [How to handle]        |
    | [Risk 2]                | ...        | ...    | ...                     |
    | [Risk 3]                | ...        | ...    | ...                     |

    ---

    Be specific, data-driven, and actionable. Every recommendation must reference
    actual companies and contacts found in this discovery session.
    """

    response = llm.invoke(prompt)
    state["recommendations"] = response.content
    return state
