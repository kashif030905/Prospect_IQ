from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME
from agents.state import ProcureAIState

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def recommendation_agent(state: ProcureAIState) -> ProcureAIState:
    """
    Recommendation Agent - Synthesises all agent outputs into a final,
    actionable sales playbook. This is the board-level summary.
    """
    prompt = f"""
    You are the Chief Revenue Officer (CRO) AI Agent for ProcureAI.

    You have received the full customer discovery analysis from 6 specialised agents.
    Your job: synthesise everything into a crisp, professional sales playbook that
    a sales team can execute starting TODAY.

    ═══════════════════════════════════════════════════════════
    FULL DISCOVERY CONTEXT
    ═══════════════════════════════════════════════════════════
    PRODUCT         : {state['product_description']}
    TARGET PERSONA  : {state['target_persona']}
    TARGET LOCATION : {state['target_location']}
    TARGET INDUSTRY : {state['target_industry']}

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

    ## 1. EXECUTIVE SUMMARY
    [3-4 sentences: what we found, how many companies, top recommendation, expected outcome]

    ---

    ## 2. TOP PROSPECT — IMMEDIATE ACTION
    Company   : [Name]
    Why #1    : [Specific comparative reasoning — what makes this the BEST opportunity]
    Score     : [X/100]
    Contact   : [Name, Title]
    Action    : [Exactly what to do in the next 24 hours]

    ---

    ## 3. PRIORITISED PROSPECT LIST

    | Priority | Company | Score | Contact | Best Channel | Why This Rank |
    |----------|---------|-------|---------|--------------|---------------|
    | 🥇 1st   | ...     | /100  | ...     | ...          | ...           |
    | 🥈 2nd   | ...     | /100  | ...     | ...          | ...           |
    | 🥉 3rd   | ...     | /100  | ...     | ...          | ...           |

    WHY THIS RANKING:
    [Paragraph comparing all 3 companies — what specific factors put #1 ahead of #2,
    why #2 is better than #3. Reference scores, pain fit, and contact quality.]

    ---

    ## 4. 14-DAY OUTREACH SEQUENCE

    Day 1  — [Specific action: who to contact, which channel, what to say]
    Day 2  — [Follow-up or next prospect action]
    Day 3  — [Action]
    Day 5  — [Action]
    Day 7  — [Action]
    Day 10 — [Action]
    Day 14 — [Final follow-up or pivot decision]

    ---

    ## 5. PROVEN EMAIL TEMPLATES

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

    ### Template B — For Prospects 2 & 3 (semi-personalized)
    Subject : [Subject line]
    Body    :
    Hi [Name],

    [Opening line]

    [Value prop]

    [CTA]

    Best,
    [Your Name]

    ---

    ## 6. EXPECTED OUTCOMES

    | Metric                  | Estimate         | Basis                    |
    |-------------------------|------------------|--------------------------|
    | Emails sent             | [n]              | 3 prospects × sequence   |
    | Expected open rate      | [%]              | Industry avg for location|
    | Expected reply rate     | [%]              | Role + channel mix       |
    | Expected meetings booked| [n]              | Reply rate × conversion  |
    | Pipeline value (est.)   | ₹[amount]        | Deal size × meetings     |
    | Time to first response  | [X-Y days]       | Typical for this persona |

    ---

    ## 7. IMMEDIATE NEXT STEPS (Today's To-Do List)

    ✅ Step 1: [Action — be specific, include who does what]
    ✅ Step 2: [Action]
    ✅ Step 3: [Action]
    ✅ Step 4: [Action]
    ✅ Step 5: [Action]

    ---

    ## 8. RISKS & MITIGATION

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