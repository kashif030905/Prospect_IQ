import streamlit as st
import re

SECTION_CSS = """
<style>
.section-header {
    font-size: 20px;
    font-weight: 700;
    margin: 20px 0 12px 0;
}
[data-theme="light"] .section-header { color: #1a202c; }
[data-theme="dark"]  .section-header { color: #ffffff; }
</style>
"""


def count_prospects(results: dict) -> int:
    """Count actual prospects from pipeline output (not recommendation placeholders)."""
    validated = results.get("validated_companies", "") or ""
    companies = results.get("companies_found", "") or ""

    for text in (validated, companies):
        n = len(re.findall(r"COMPANY NAME\s*:", text, re.I))
        if n:
            return n
        n = len(re.findall(r"COMPANY\s*:\s*", text, re.I))
        if n:
            return n

    return 0


def _field(text, key):
    m = re.search(rf"{re.escape(key)}\s*:\s*(.+)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _clean(text):
    text = re.sub(r"[│╔╠╚╗╣╝║├┤┌┘└┐═]", "", text)
    text = re.sub(r"─+", "", text)
    return text.strip()


def _verdict_badge(verdict):
    v = verdict.lower()
    if "pursue now" in v or "strong" in v:
        return f"✅ {verdict}"
    if "qualify" in v or "medium" in v:
        return f"⚠️ {verdict}"
    if "skip" in v or "disqualified" in v:
        return f"❌ {verdict}"
    return verdict


def _confidence_badge(conf):
    c = conf.lower()
    if c == "high":
        return "🟢 High"
    if c == "medium":
        return "🟡 Medium"
    if c == "low":
        return "🔴 Low"
    return conf or "—"


def _extract_score_from_block(block: str) -> int | None:
    for pat in (
        r"TOTAL SCORE\s*:\s*(\d+)\s*/\s*100",
        r"TOTAL SCORE\s*:\s*(\d+)",
        r"Score\s*:\s*(\d+)\s*/\s*100",
    ):
        m = re.search(pat, block, re.I)
        if m:
            return min(int(m.group(1)), 100)

    parts = re.findall(
        r"(?:Location Match|Industry Fit|Size Match|Pain Point Fit|Growth Signals)\s*:\s*(\d+)\s*/",
        block,
        re.I,
    )
    if parts:
        total = sum(int(p) for p in parts)
        if total > 0:
            return min(total, 100)
    return None


def _extract_scores_map(text: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    if not text:
        return scores

    text = _clean(text)
    blocks = re.split(r"COMPANY\s*\d*\s*:", text)
    for block in blocks:
        block = block.strip()
        if len(block) < 10:
            continue
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        name = re.sub(r"[│┌╔#*|]", "", lines[0]).strip()
        if not name or len(name) < 2:
            continue
        score = _extract_score_from_block(block)
        if score is not None:
            scores[name.lower()] = score

    for m in re.finditer(
        r"\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*[^|]*\|\s*(\d+)\s*/?\s*100\s*\|",
        text,
    ):
        company = m.group(1).strip()
        if company and company.lower() not in scores:
            scores[company.lower()] = int(m.group(2))

    return scores


def _lookup_score(scores: dict[str, int], company: str) -> int | None:
    if not company:
        return None
    key = company.lower().strip()
    if key in scores:
        return scores[key]
    for k, v in scores.items():
        if k in key or key in k:
            return v
    return None


def _strip_section_number(title: str) -> str:
    return re.sub(r"^\d+\.\s*", "", title).strip()


def _parse_key_value_body(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in body.split("\n"):
        line = line.strip()
        if ":" not in line or line.startswith("|"):
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip()
        if key and val:
            fields[key] = val
    return fields


def _parse_score_value(raw: str) -> int | None:
    if not raw:
        return None
    m = re.search(r"(\d+)", raw)
    return min(int(m.group(1)), 100) if m else None


def _score_color(score):
    try:
        s = int(re.search(r"\d+", str(score)).group())
        if s >= 80:
            return s, "🟢"
        if s >= 60:
            return s, "🟡"
        if s >= 40:
            return s, "🟠"
        return s, "🔴"
    except Exception:
        return None, "⚪"


# ── Renderers ─────────────────────────────────────────────

def _render_icp(text):
    text = text or ""
    st.markdown('<div class="section-header">🧩 Ideal Customer Profile</div>', unsafe_allow_html=True)
    if len(text.strip()) < 10:
        st.info("No ICP profile generated yet.")
        return
    with st.container(border=True):
        st.markdown(_clean(text))


def _render_companies(text):
    st.markdown('<div class="section-header">🏢 Companies Found</div>', unsafe_allow_html=True)
    if not text or len(text.strip()) < 10:
        st.info("No companies found yet.")
        return

    blocks = re.split(r"={30,}", text)
    rendered = 0

    for block in blocks:
        if "COMPANY NAME" not in block and "COMPANY" not in block:
            continue
        name = _field(block, "COMPANY NAME") or _field(block, "COMPANY")
        if not name:
            continue

        website = _field(block, "WEBSITE")
        location = _field(block, "LOCATION")
        industry = _field(block, "INDUSTRY")
        size = _field(block, "COMPANY SIZE")
        what = _field(block, "WHAT THEY DO")
        why = _field(block, "WHY THEY MATCH")

        with st.container(border=True):
            st.markdown(f"### 🏢 {name}")
            if website:
                st.markdown(f"🔗 [{website}]({website})")

            tags = []
            if location:
                tags.append(f"📍 {location}")
            if industry:
                tags.append(f"🏭 {industry}")
            if size:
                tags.append(f"👥 {size}")
            if tags:
                st.caption(" · ".join(tags))

            if what:
                st.markdown("**What they do**")
                st.write(what)
            if why:
                st.success(f"**Why they match:** {why}")

        rendered += 1

    if rendered == 0:
        st.markdown(_clean(text))


def _render_validated(text):
    st.markdown('<div class="section-header">✅ Validated Companies</div>', unsafe_allow_html=True)
    if not text or len(text.strip()) < 10:
        st.info("No validated companies yet.")
        return

    text = _clean(text)
    blocks = re.split(r"COMPANY\s*\d*\s*:", text)
    rendered = 0

    for block in blocks:
        block = block.strip()
        if len(block) < 20:
            continue
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        company_name = re.sub(r"[│┌╔#*|]", "", lines[0]).strip()
        if any(x in company_name.upper() for x in ["VALIDATION", "REPORT", "CONTEXT", "RULE", "OUTPUT", "SCORES"]):
            continue
        if len(company_name) < 2:
            continue

        score = _extract_score_from_block(block)
        verdict_m = re.search(r"VERDICT\s*:\s*([^\n]+)", block)
        icp_m = re.search(r"ICP MATCH\s*:\s*([^\n]+)", block)
        website_m = re.search(r"WEBSITE\s*:\s*(\S+)", block)
        why_m = re.search(r"WHY WE SHOULD PURSUE(.*?)(?:RISKS|VERDICT|$)", block, re.DOTALL | re.IGNORECASE)
        risk_m = re.search(r"RISKS\s*/?\s*CONCERNS?(.*?)(?:VERDICT|$)", block, re.DOTALL | re.IGNORECASE)

        verdict = verdict_m.group(1).strip() if verdict_m else ""
        icp = icp_m.group(1).strip() if icp_m else ""
        website = website_m.group(1).strip() if website_m else ""
        why_text = re.sub(r"\n+", " ", why_m.group(1)).strip()[:300] if why_m else ""
        risk_text = re.sub(r"\n+", " ", risk_m.group(1)).strip()[:300] if risk_m else ""
        why_text = re.sub(r"\d+/\d+\s*\[.*?\]", "", why_text).strip()
        risk_text = re.sub(r"\d+/\d+\s*\[.*?\]", "", risk_text).strip()

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### 🏢 {company_name}")
                if website and website.startswith("http"):
                    st.markdown(f"🔗 [{website}]({website})")
            with col2:
                if score is not None:
                    st.metric("ICP Score", f"{score}/100")
                verdict_label = _verdict_badge(verdict) if verdict else ""
                if verdict_label:
                    st.caption(verdict_label)

            if icp:
                st.markdown(f"**ICP Match:** {icp}")
            if score is not None:
                st.progress(score / 100)
            if why_text:
                st.info(f"💡 {why_text}")
            if risk_text:
                st.warning(f"⚠️ {risk_text}")

            clean_block = re.sub(r"\s{2,}", "\n", block)
            clean_block = re.sub(r"─+|={3,}", "\n---\n", clean_block)
            with st.expander("📋 Full Details"):
                st.markdown(clean_block)

        rendered += 1

    if rendered == 0:
        st.markdown(text)

    table_m = re.search(r"\|[\s]*Rank.*?(?=\n\n|\Z)", text, re.DOTALL)
    if table_m:
        st.divider()
        st.markdown("#### 📊 Comparison Table")
        st.markdown(table_m.group(0))

    shortlist_m = re.search(r"(?:FINAL SHORTLIST|TOP 3)(.*?)(?=\n\n\n|\Z)", text, re.DOTALL | re.IGNORECASE)
    if shortlist_m:
        st.divider()
        st.markdown("#### 🏆 Final Shortlist")
        st.markdown(re.sub(r"─+|={3,}", "", shortlist_m.group(0)))


def _render_decision_makers(text):
    st.markdown('<div class="section-header">👤 Decision Makers</div>', unsafe_allow_html=True)
    if not text or len(text.strip()) < 10:
        st.info("No decision makers found yet.")
        return

    text = _clean(text)
    blocks = re.split(r"COMPANY\s*:", text)
    rendered = 0

    for block in blocks:
        if len(block.strip()) < 20:
            continue
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        company_name = re.sub(r"[│┌╔#*|]", "", lines[0]).strip() if lines else "Company"

        name = _field(block, "Full Name")
        title = _field(block, "Job Title")
        dept = _field(block, "Department")
        location = _field(block, "Location")
        seniority = _field(block, "Seniority")
        confidence = _field(block, "Confidence")
        linkedin = _field(block, "LinkedIn URL")
        why_m = re.search(
            r"WHY THIS PERSON\s*:(.*?)(?:HOW TO FIND|ADDITIONAL|LinkedIn Search|$)",
            block, re.DOTALL | re.IGNORECASE
        )
        why = re.sub(r"\n+", " ", why_m.group(1)).strip()[:300] if why_m else ""

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### 👤 {name or 'To be verified'}")
                st.caption(f"🏢 {company_name}  ·  💼 {title or '—'}")
            with col2:
                if confidence:
                    st.markdown(f"**Confidence**")
                    st.markdown(_confidence_badge(confidence))

            tags = []
            if location:
                tags.append(f"📍 {location}")
            if dept:
                tags.append(f"🏛️ {dept}")
            if seniority:
                tags.append(f"⭐ {seniority}")
            if tags:
                st.caption(" · ".join(tags))

            if why:
                st.info(f"💡 {why}")

            if linkedin and linkedin.startswith("http"):
                st.markdown(f"🔗 [LinkedIn Profile]({linkedin})")
            else:
                st.caption("🔗 Search manually on LinkedIn")

        rendered += 1

    if rendered == 0:
        st.markdown(text)

    if "OUTREACH PRIORITY SUMMARY" in text:
        st.divider()
        summary = text.split("OUTREACH PRIORITY SUMMARY")[-1]
        with st.expander("📋 Outreach Priority Summary", expanded=True):
            st.markdown(_clean(summary))


def _render_enriched(text):
    st.markdown('<div class="section-header">📬 Enriched Contacts</div>', unsafe_allow_html=True)
    if not text or len(text.strip()) < 10:
        st.info("No enriched contacts yet.")
        return

    text = _clean(text)
    blocks = re.split(r"CONTACT\s*:", text)
    rendered = 0

    for block in blocks:
        if len(block.strip()) < 20:
            continue
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        header = re.sub(r"[║╔#*|]", "", lines[0]).strip() if lines else "Contact"

        email = _field(block, "Email")
        linkedin = _field(block, "LinkedIn")
        phone = _field(block, "Phone")
        channel = _field(block, "Best Channel")
        hook = _field(block, "Hook")
        subject = _field(block, "Subject Line")
        opening = _field(block, "Opening Line")
        value = _field(block, "Value Prop")
        cta = _field(block, "CTA")

        with st.container(border=True):
            st.markdown(f"### 📬 {header}")
            st.divider()

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**📧 Email**")
                st.write(email or "Not found")
            with c2:
                st.markdown("**🔗 LinkedIn**")
                if linkedin and linkedin.startswith("http"):
                    st.markdown(f"[View Profile]({linkedin})")
                else:
                    st.write(linkedin or "Search manually")
            with c3:
                st.markdown("**📱 Phone**")
                st.write(phone or "Not available")

            if channel:
                st.info(f"✅ **Best Channel:** {channel}")
            if hook:
                st.success(f"🪝 **Hook:** {hook}")

            if subject or opening:
                with st.expander("📝 Email Template"):
                    if subject:
                        st.markdown(f"**Subject:** {subject}")
                    if opening:
                        st.markdown(f"**Opening:** {opening}")
                    if value:
                        st.markdown(f"**Value Prop:** {value}")
                    if cta:
                        st.markdown(f"**CTA:** {cta}")

        rendered += 1

    if rendered == 0:
        st.markdown(text)

    if "OUTREACH STRATEGY OVERVIEW" in text:
        st.divider()
        strategy = text.split("OUTREACH STRATEGY OVERVIEW")[-1]
        with st.expander("🗺️ Outreach Strategy Overview", expanded=True):
            st.markdown(_clean(strategy))


def _extract_company_names_validated(text: str) -> list[str]:
    names: list[str] = []
    if not text:
        return names
    for block in re.split(r"COMPANY\s*\d*\s*:", _clean(text)):
        block = block.strip()
        if len(block) < 10:
            continue
        name = re.sub(r"[│┌╔#*|]", "", block.split("\n")[0]).strip()
        if name and len(name) > 2 and name.upper() not in {"VALIDATION", "REPORT", "SCORES"}:
            names.append(name)
    return names


def _build_priority_rows(body: str, scores_map: dict[str, int], validated: str) -> list[dict]:
    rows: list[dict] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("|--") or "Priority" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        company = cells[1] if len(cells) > 1 else ""
        if not company or company.lower() in ("...", "company", "tbd"):
            continue

        score_raw = cells[2] if len(cells) > 2 else ""
        score = _parse_score_value(score_raw) or _lookup_score(scores_map, company)
        if score is None or score_raw.strip() in ("/100", "...", "?", "N/A", "Awaiting score from validation"):
            score = _lookup_score(scores_map, company)

        row = {
            "Priority": cells[0],
            "Company": company,
            "Score": f"{score}/100" if score is not None else "—",
            "Contact": cells[3] if len(cells) > 3 else "—",
            "Best Channel": cells[4] if len(cells) > 4 else "—",
            "Why This Rank": cells[5] if len(cells) > 5 else "—",
        }
        rows.append(row)

    if rows:
        return rows

    names = _extract_company_names_validated(validated)
    ranked = [(name, _lookup_score(scores_map, name)) for name in names]
    ranked = [(n, s) for n, s in ranked if s is not None]
    ranked.sort(key=lambda x: x[1], reverse=True)
    medals = ["1st", "2nd", "3rd"]
    for i, (name, score) in enumerate(ranked):
        rows.append({
            "Priority": medals[i] if i < len(medals) else f"{i + 1}th",
            "Company": name,
            "Score": f"{score}/100",
            "Contact": "—",
            "Best Channel": "—",
            "Why This Rank": "—",
        })
    return rows


def _render_recommendation(text, results: dict | None = None):
    st.markdown('<div class="section-header">🎯 Final Recommendation</div>', unsafe_allow_html=True)
    if not text or len(text.strip()) < 10:
        st.info("No recommendation yet.")
        return

    results = results or {}
    validated = results.get("validated_companies", "") or ""
    scores_map = _extract_scores_map(validated)

    sections = re.split(r"##\s+", text)
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().split("\n")
        raw_title = lines[0].strip()
        title = _strip_section_number(raw_title)
        body = "\n".join(lines[1:]).strip()
        if not body and "EXECUTIVE" not in title.upper():
            continue
        t = title.upper()

        if "EXECUTIVE SUMMARY" in t:
            with st.container(border=True):
                st.markdown("### Executive Summary")
                st.markdown(body)

        elif "TOP PROSPECT" in t:
            fields = _parse_key_value_body(body)
            company = fields.get("company", "")
            score = _lookup_score(scores_map, company) or _parse_score_value(fields.get("score", ""))

            with st.container(border=True):
                st.markdown("### Top Prospect — Immediate Action")
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{company or 'See details below'}**")
                with c2:
                    if score is not None:
                        st.metric("ICP Score", f"{score}/100")

                for label, key in (
                    ("Why they're #1", "why #1"),
                    ("Contact", "contact"),
                    ("Next action", "action"),
                ):
                    if key in fields:
                        st.markdown(f"**{label}:** {fields[key]}")

                extra = {k: v for k, v in fields.items()
                         if k not in ("company", "score", "why #1", "contact", "action")}
                for key, val in extra.items():
                    st.markdown(f"**{key.title()}:** {val}")

        elif "PRIORITISED" in t or "PRIORITIZED" in t:
            st.markdown("### Prioritised Prospect List")
            table_rows = _build_priority_rows(body, scores_map, validated)
            if table_rows:
                st.dataframe(table_rows, use_container_width=True, hide_index=True)
            else:
                st.markdown(body)

            ranking_m = re.search(
                r"WHY THIS RANKING\s*:(.*?)(?:\n---|\n##|\Z)",
                body,
                re.DOTALL | re.IGNORECASE,
            )
            if ranking_m:
                ranking_text = ranking_m.group(1).strip()
                if ranking_text:
                    st.markdown("**Why this ranking**")
                    st.markdown(ranking_text)

        elif "14-DAY" in t or ("SEQUENCE" in t and "OUTREACH" in t):
            with st.expander("14-Day Outreach Sequence"):
                st.markdown(body)

        elif "EMAIL TEMPLATE" in t or "PROVEN EMAIL" in t:
            with st.expander("Email Templates"):
                st.markdown(body)

        elif "NEXT STEPS" in t or "IMMEDIATE NEXT" in t:
            with st.container(border=True):
                st.markdown("### Immediate Next Steps")
                st.markdown(body)

        elif "RISKS" in t:
            with st.expander("Risks & Mitigation"):
                st.markdown(body)

        elif "EXPECTED OUTCOMES" in t:
            st.markdown("### Expected Outcomes")
            st.markdown(body)

        else:
            if body:
                st.markdown(f"### {title}")
                st.markdown(body)


def render_results_section(results: dict):
    st.markdown(SECTION_CSS, unsafe_allow_html=True)
    st.header("📊 Customer Discovery Results")

    prospect_count = count_prospects(results)
    if prospect_count:
        st.caption(f"Found **{prospect_count}** validated prospect{'s' if prospect_count != 1 else ''}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🧩 ICP Profile",
        "🏢 Companies Found",
        "✅ Validated",
        "👤 Decision Makers",
        "📬 Enriched Contacts",
        "🎯 Recommendation"
    ])

    with tab1:
        _render_icp(results.get("icp_profile", ""))
    with tab2:
        _render_companies(results.get("companies_found", ""))
    with tab3:
        _render_validated(results.get("validated_companies", ""))
    with tab4:
        _render_decision_makers(results.get("decision_makers", ""))
    with tab5:
        _render_enriched(results.get("enriched_contacts", ""))
    with tab6:
        _render_recommendation(results.get("recommendations", ""), results)
