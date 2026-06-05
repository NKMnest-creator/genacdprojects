import html
import json
import os
import re
from pathlib import Path

import anthropic
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResilienceRadar",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
html, body, .stApp { background-color: #0d1117 !important; }
.stApp > header { background-color: #0d1117 !important; }
#MainMenu, footer, .stDeployButton { display: none !important; }

/* Constrain & center content */
.main .block-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 0.5rem 1.5rem 4rem;
}
/* Remove Streamlit's default top gap */
[data-testid="stAppViewContainer"] > section > div:first-child {
    padding-top: 0 !important;
}
div[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: 0 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 6px;
    border-bottom: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: 1px solid #21262d !important;
    border-bottom: none !important;
    border-radius: 6px 6px 0 0 !important;
    color: #8b949e !important;
    font-size: 12px !important;
    padding: 6px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(14,165,233,0.1) !important;
    border-color: #0ea5e9 !important;
    color: #38bdf8 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 16px 0 0 !important; }

/* Selectbox */
.stSelectbox div[data-baseweb="select"] > div {
    background: #161b22 !important;
    border-color: #21262d !important;
    color: #c9d1d9 !important;
    min-height: 38px;
}
.stSelectbox div[data-baseweb="select"] > div:focus-within {
    border-color: #0ea5e9 !important;
}
ul[data-baseweb="menu"] { background: #161b22 !important; border: 1px solid #21262d !important; }
li[data-baseweb="menu-item"]:hover { background: #21262d !important; }

/* Buttons */
.stButton > button {
    background: #0ea5e9 !important;
    color: #fff !important;
    border: none !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    height: 38px;
    transition: background 0.15s;
}
.stButton > button:hover { background: #0284c7 !important; }

/* Radio (outreach toggle) */
div[role="radiogroup"] {
    flex-direction: row !important;
    gap: 6px !important;
    margin-bottom: 10px;
}
div[role="radiogroup"] label {
    background: none !important;
    border: 1px solid #21262d !important;
    border-radius: 5px !important;
    padding: 4px 12px !important;
    cursor: pointer !important;
    color: #8b949e !important;
    font-size: 11px !important;
    margin: 0 !important;
}
div[role="radiogroup"] label:has(input:checked) {
    background: rgba(14,165,233,0.1) !important;
    border-color: #0ea5e9 !important;
    color: #38bdf8 !important;
}
div[role="radiogroup"] label span { color: inherit !important; }
div[role="radiogroup"] label input { display: none !important; }

/* Spinner color */
.stSpinner > div { border-top-color: #0ea5e9 !important; }

/* Misc */
hr { border-color: #21262d !important; }
.element-container { margin-bottom: 0 !important; }
[data-testid="column"] { padding: 0 4px !important; }
.stAlert { background: #161b22 !important; border-color: #21262d !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Load companies CSV ─────────────────────────────────────────────────────────
CSV_PATH = Path(__file__).parent / "List of Companies - for buy Sentiment review.csv"

@st.cache_data
def load_companies() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH)

# ── Claude API ─────────────────────────────────────────────────────────────────
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")


def call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY environment variable is not set.")
        return None
    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as e:
        st.error(f"Claude API error: {e}")
        return None
    return "".join(b.text for b in response.content if b.type == "text")


def parse_json(raw: str) -> dict | None:
    # Strip markdown code fences if present
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Grab outermost {...}
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def generate_company_brief(company_name: str, sc_risk: str, industry: str) -> str | None:
    system = (
        "You are a supply chain intelligence analyst helping B2B SaaS sales teams identify "
        "high-fit prospects. Be specific, cite only real URLs found via web search, and only "
        "use information from December 2025 through June 2026. "
        "Return only valid JSON — no preamble, no explanation, no markdown fences."
    )
    user = f"""Research and generate a supply chain intelligence brief for {company_name}.
Primary SC risk: {sc_risk}
Industry: {industry}

Use web search to find recent news, earnings calls, press releases, and filings for {company_name}.
Only include events and information from December 2025 – June 2026.

Return ONLY this JSON object (no other text, no markdown):
{{
  "signal_badge": "HIGH",
  "csuite_priorities": [
    "Priority 1",
    "Priority 2",
    "Priority 3",
    "Priority 4"
  ],
  "sc_risk_signals": [
    {{"text": "Signal description", "source_name": "Source Name", "source_url": "https://real-url"}},
    {{"text": "Signal description", "source_name": "Source Name", "source_url": "https://real-url"}},
    {{"text": "Signal description", "source_name": "Source Name", "source_url": "https://real-url"}},
    {{"text": "Signal description", "source_name": "Source Name", "source_url": "https://real-url"}}
  ],
  "signal_scores": {{
    "supply_chain_urgency": 75,
    "executive_awareness": 60,
    "recent_news_volume": 80,
    "budget_signals": 45
  }},
  "recent_news": [
    {{"headline": "Headline", "source_url": "https://real-url", "date": "Jan 2026", "tag": "SUPPLY CHAIN"}},
    {{"headline": "Headline", "source_url": "https://real-url", "date": "Feb 2026", "tag": "EARNINGS"}},
    {{"headline": "Headline", "source_url": "https://real-url", "date": "Mar 2026", "tag": "RISK EVENT"}},
    {{"headline": "Headline", "source_url": "https://real-url", "date": "Apr 2026", "tag": "SUPPLY CHAIN"}}
  ],
  "outreach": {{
    "email": "Subject: [Specific subject line]\\n\\nHi [Name],\\n\\n[Body referencing specific signals found. End with soft CTA for a 20-min call.]\\n\\n[Your name]",
    "call_opener": "[Opening line citing a specific signal. Transition to value prop. Ask for meeting.]",
    "linkedin": "[Short message citing a specific signal. Peer tone. Soft CTA.]"
  }}
}}

Scoring rubric — apply this consistently across all four dimensions:
- 80-100: Explicitly named by C-suite in earnings call or investor presentation, OR multiple independent sources confirm it as a primary theme
- 50-79: Mentioned in a press release, analyst call, or news article but not a dominant theme
- 20-49: Indirect reference only — inferred from context, mentioned in passing, or a single brief mention
- 0-19: No evidence found in the Dec 2025 – Jun 2026 data window

Apply each dimension as follows:
- supply_chain_urgency: how strongly and recently has the company flagged SC disruption or risk publicly
- executive_awareness: has C-suite named SC resilience, investment, or risk mitigation specifically
- recent_news_volume: how much SC-related news coverage exists in the data window (0-19 = none, 20-49 = 1-2 articles, 50-79 = 3-5 articles, 80-100 = 6+ articles or major outlet coverage)
- budget_signals: any indication of SC technology investment, vendor evaluation, RFPs, or CapEx earmarked for SC resilience

signal_badge: HIGH if supply_chain_urgency >= 70 OR two or more dimensions >= 70, MEDIUM if any dimension is 50-69, LOW if all dimensions below 50
- source_url: use empty string "" if no real URL — never fabricate a URL
- tag must be exactly one of: SUPPLY CHAIN, EARNINGS, RISK EVENT
- outreach must reference specific signals found, not generic supply chain content"""
    return call_claude(system, user, max_tokens=4000)


def generate_industry_summary(industry: str, companies_df: pd.DataFrame) -> str | None:
    company_list = ", ".join(companies_df["company_name"].tolist())
    risks = ", ".join(companies_df["primary_sc_risk"].unique().tolist())
    system = (
        "You are a supply chain intelligence analyst. Synthesize industry supply chain themes "
        "for B2B SaaS sales teams. Only use information from December 2025 through June 2026. "
        "Write for a busy AE — clear and direct, no jargon. Return only valid JSON."
    )
    user = f"""Research and generate an industry supply chain intelligence summary for: {industry}

Companies: {company_list}
Risk categories present: {risks}

Search for dominant SC themes, earnings commentary, and risk events across this industry Dec 2025–Jun 2026.

Return ONLY this JSON object (no other text):
{{
  "summary": "3–5 sentence synthesis of dominant SC themes across this industry. Write for a busy AE.",
  "theme_pills": ["Theme 1", "Theme 2", "Theme 3", "Theme 4", "Theme 5"],
  "company_rows": [
    {{"company": "Company Name", "signal_summary": "One-line signal summary", "badge": "HIGH"}},
    {{"company": "Company Name", "signal_summary": "One-line signal summary", "badge": "MEDIUM"}},
    {{"company": "Company Name", "signal_summary": "One-line signal summary", "badge": "LOW"}}
  ]
}}

company_rows must include exactly one entry per company in this list: {company_list}
badge must be HIGH, MEDIUM, or LOW based on signals found in Dec 2025–Jun 2026."""
    return call_claude(system, user, max_tokens=3000)


# ── HTML building blocks ───────────────────────────────────────────────────────

def signal_badge(level: str) -> str:
    level = level.upper()
    cfg = {
        "HIGH":   ("rgba(239,68,68,0.1)",   "#ef4444", "🔴"),
        "MEDIUM": ("rgba(245,158,11,0.1)",  "#f59e0b", "🟡"),
        "LOW":    ("rgba(16,185,129,0.1)",  "#10b981", "🟢"),
    }
    bg, color, emoji = cfg.get(level, cfg["LOW"])
    return (
        f'<span style="font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px;'
        f'background:{bg};color:{color};border:1px solid {color}33">'
        f'{emoji} {level} SIGNAL</span>'
    )


def score_bar(label: str, score: int) -> str:
    score = max(0, min(100, int(score)))
    return (
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">'
        f'<div style="font-size:11px;color:#c9d1d9;width:160px;flex-shrink:0">{html.escape(label)}</div>'
        f'<div style="flex:1;height:4px;background:#21262d;border-radius:2px;overflow:hidden">'
        f'<div style="width:{score}%;height:100%;background:linear-gradient(90deg,#10b981,#34d399);border-radius:2px"></div>'
        f'</div>'
        f'<div style="font-size:11px;color:#38bdf8;width:28px;text-align:right">{score}</div>'
        f'</div>'
    )


def news_tag(tag: str) -> str:
    cfg = {
        "SUPPLY CHAIN": ("rgba(14,165,233,0.1)", "#38bdf8"),
        "EARNINGS":     ("rgba(16,185,129,0.1)", "#10b981"),
        "RISK EVENT":   ("rgba(239,68,68,0.1)",  "#ef4444"),
    }
    bg, color = cfg.get(tag.upper(), cfg["SUPPLY CHAIN"])
    return (
        f'<span style="font-size:9px;padding:2px 6px;border-radius:3px;'
        f'background:{bg};color:{color}">{html.escape(tag)}</span>'
    )


def panel(title: str, body: str, mt: str = "0") -> str:
    return (
        f'<div style="background:#161b22;border:1px solid #21262d;border-radius:8px;'
        f'padding:12px 14px;margin-top:{mt}">'
        f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;'
        f'color:#0ea5e9;margin-bottom:8px">{html.escape(title)}</div>'
        f'{body}</div>'
    )


def bullet(text: str, src_name: str = "", src_url: str = "") -> str:
    link = ""
    if src_url:
        link = (
            f' <a href="{html.escape(src_url)}" target="_blank" '
            f'style="color:#38bdf8;font-size:10px">[{html.escape(src_name)} ↗]</a>'
        )
    elif src_name:
        link = f' <span style="color:#6b7280;font-size:10px">[{html.escape(src_name)}]</span>'
    return (
        f'<div style="display:flex;gap:7px;margin-bottom:6px">'
        f'<div style="width:4px;height:4px;background:#0ea5e9;border-radius:50%;'
        f'margin-top:5px;flex-shrink:0"></div>'
        f'<p style="font-size:11px;color:#c9d1d9;line-height:1.5;margin:0">'
        f'{html.escape(text)}{link}</p></div>'
    )


EMPTY_STATE = (
    '<div style="text-align:center;padding:48px 0;color:#6b7280;font-size:12px">'
    'Select an option above and click ⚡ to generate intelligence</div>'
)

# ── App layout ─────────────────────────────────────────────────────────────────
df = load_companies()

st.markdown(
    '<h1 style="font-size:20px;font-weight:700;color:#fff;margin-bottom:4px">📡 ResilienceRadar</h1>'
    '<div style="font-size:11px;color:#6b7280;margin-bottom:20px">'
    'Supply chain intelligence · 30 companies · 6 industries</div>',
    unsafe_allow_html=True,
)

tab_co, tab_ind = st.tabs(["Company View", "Industry View"])

# ══════════════════════════════════════════════════════════════════════════════
# COMPANY VIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_co:
    st.markdown(
        '<div style="border-left:2px solid #0ea5e9;padding:8px 12px;margin-bottom:16px;'
        'background:rgba(14,165,233,0.04);border-radius:0 6px 6px 0">'
        '<span style="font-size:11px;color:#6b7280;line-height:1.6">'
        'Pick any of the 30 tracked companies and click <strong style="color:#8b949e">⚡ Generate Brief</strong> '
        'to get a live intelligence brief — C-suite priorities, supply chain risk signals, '
        'urgency scores, recent news, and ready-to-send outreach copy. '
        'All signals are sourced from public news and earnings within Dec 2025 – Jun 2026.'
        '</span></div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([5, 1])
    with c1:
        selected_co = st.selectbox(
            "company", sorted(df["company_name"].tolist()), label_visibility="collapsed"
        )
    with c2:
        gen_co = st.button("⚡ Generate Brief", key="btn_co", use_container_width=True)

    if gen_co:
        row = df[df["company_name"] == selected_co].iloc[0]
        with st.spinner(f"Researching {selected_co}…"):
            raw = generate_company_brief(
                row["company_name"], row["primary_sc_risk"], row["industry"]
            )
        if raw:
            parsed = parse_json(raw)
            if parsed:
                st.session_state[f"co::{selected_co}"] = parsed
            else:
                st.error("Could not parse the response. Raw output shown below.")
                st.code(raw, language="text")

    key_co = f"co::{selected_co}"
    if key_co in st.session_state:
        d = st.session_state[key_co]
        row = df[df["company_name"] == selected_co].iloc[0]

        # Company header
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;background:#161b22;'
            f'border:1px solid #21262d;border-radius:8px;padding:12px 14px;margin:12px 0">'
            f'<div style="width:36px;height:36px;background:#fff;border-radius:6px;display:flex;'
            f'align-items:center;justify-content:center;font-size:9px;font-weight:700;'
            f'color:#000;flex-shrink:0">{html.escape(str(row["ticker"]))}</div>'
            f'<div>'
            f'<div style="font-weight:700;color:#fff;font-size:14px">'
            f'{html.escape(row["company_name"])}</div>'
            f'<div style="font-size:11px;color:#6b7280;margin-top:2px">'
            f'{html.escape(row["industry"])} · {html.escape(row["hq_country"])} · '
            f'{html.escape(row["primary_sc_risk"])}</div>'
            f'</div>'
            f'<div style="margin-left:auto">{signal_badge(d.get("signal_badge", "LOW"))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # C-Suite + SC Risk Signals side by side
        left, right = st.columns(2)
        with left:
            body = "".join(bullet(p) for p in d.get("csuite_priorities", []))
            st.markdown(panel("C-Suite Priorities", body), unsafe_allow_html=True)
        with right:
            body = "".join(
                bullet(s.get("text", ""), s.get("source_name", ""), s.get("source_url", ""))
                for s in d.get("sc_risk_signals", [])
            )
            st.markdown(panel("Supply Chain Risk Signals", body), unsafe_allow_html=True)

        # Signal scores
        sc = d.get("signal_scores", {})
        scores_html = (
            score_bar("Supply chain urgency", sc.get("supply_chain_urgency", 0))
            + score_bar("Executive awareness",   sc.get("executive_awareness", 0))
            + score_bar("Recent news volume",    sc.get("recent_news_volume", 0))
            + score_bar("Budget signals",        sc.get("budget_signals", 0))
        )
        st.markdown(panel("Signal Score", scores_html, mt="10px"), unsafe_allow_html=True)

        # Recent news
        news_html = ""
        for item in d.get("recent_news", []):
            url = item.get("source_url", "")
            src_link = (
                f' <a href="{html.escape(url)}" target="_blank" '
                f'style="color:#38bdf8;font-size:10px">[↗]</a>'
            ) if url else ""
            news_html += (
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
                f'padding:8px 0;border-bottom:1px solid #21262d">'
                f'<div style="flex:1;padding-right:10px">'
                f'<div style="font-size:11px;color:#c9d1d9;line-height:1.5">'
                f'{html.escape(item.get("headline",""))}{src_link}</div>'
                f'{news_tag(item.get("tag","SUPPLY CHAIN"))}'
                f'</div>'
                f'<div style="font-size:10px;color:#6b7280;white-space:nowrap">'
                f'{html.escape(item.get("date",""))}</div>'
                f'</div>'
            )
        st.markdown(
            panel("Recent News · Dec 2025 – Jun 2026", news_html, mt="10px"),
            unsafe_allow_html=True,
        )

        # Outreach toggle
        outreach = d.get("outreach", {})
        otype = st.radio(
            "outreach_type",
            ["✉ Email", "📞 Call Opener", "💼 LinkedIn"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"otype::{selected_co}",
        )
        key_map = {"✉ Email": "email", "📞 Call Opener": "call_opener", "💼 LinkedIn": "linkedin"}
        content = outreach.get(key_map[otype], "")
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #21262d;border-radius:8px;'
            f'padding:12px 14px;margin-top:4px">'
            f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;'
            f'color:#0ea5e9;margin-bottom:8px">Suggested Outreach</div>'
            f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:6px;'
            f'padding:12px 14px;font-size:11px;color:#8b949e;line-height:1.7;white-space:pre-wrap">'
            f'{html.escape(content)}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(EMPTY_STATE, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INDUSTRY VIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_ind:
    st.markdown(
        '<div style="border-left:2px solid #0ea5e9;padding:8px 12px;margin-bottom:16px;'
        'background:rgba(14,165,233,0.04);border-radius:0 6px 6px 0">'
        '<span style="font-size:11px;color:#6b7280;line-height:1.6">'
        'Select an industry and click <strong style="color:#8b949e">⚡ Summarize</strong> '
        'to get a sector-level view — dominant supply chain themes, key risk threads, '
        'and a signal rating for every company in that industry. '
        'Use this to prioritise which accounts to research first.'
        '</span></div>',
        unsafe_allow_html=True,
    )
    industries = df["industry"].unique().tolist()
    i1, i2 = st.columns([5, 1])
    with i1:
        selected_ind = st.selectbox(
            "industry", industries, label_visibility="collapsed", key="ind_sel"
        )
    with i2:
        gen_ind = st.button("⚡ Summarize", key="btn_ind", use_container_width=True)

    if gen_ind:
        ind_df = df[df["industry"] == selected_ind]
        with st.spinner(f"Analyzing {selected_ind}…"):
            raw = generate_industry_summary(selected_ind, ind_df)
        if raw:
            parsed = parse_json(raw)
            if parsed:
                st.session_state[f"ind::{selected_ind}"] = parsed
            else:
                st.error("Could not parse the response. Raw output shown below.")
                st.code(raw, language="text")

    key_ind = f"ind::{selected_ind}"
    if key_ind in st.session_state:
        d = st.session_state[key_ind]

        # Industry summary
        st.markdown(
            f'<div style="background:#161b22;border-left:2px solid #0ea5e9;'
            f'border-radius:0 8px 8px 0;padding:12px 14px;margin-bottom:12px;'
            f'font-size:12px;color:#8b949e;line-height:1.7">'
            f'{html.escape(d.get("summary",""))}</div>',
            unsafe_allow_html=True,
        )

        # Theme pills
        pills = "".join(
            f'<span style="font-size:10px;padding:3px 10px;border-radius:20px;'
            f'background:#161b22;border:1px solid #21262d;color:#8b949e">'
            f'{html.escape(p)}</span>'
            for p in d.get("theme_pills", [])
        )
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px">{pills}</div>',
            unsafe_allow_html=True,
        )

        # Company rows
        badge_cfg = {
            "HIGH":   ("rgba(239,68,68,0.1)",   "#ef4444"),
            "MEDIUM": ("rgba(245,158,11,0.1)",  "#f59e0b"),
            "LOW":    ("rgba(16,185,129,0.1)",  "#10b981"),
        }
        rows = ""
        for item in d.get("company_rows", []):
            name = item.get("company", "")
            match = df[df["company_name"] == name]
            ticker = str(match["ticker"].values[0]) if len(match) else name[:4].upper()
            badge = item.get("badge", "LOW").upper()
            bg, color = badge_cfg.get(badge, badge_cfg["LOW"])
            rows += (
                f'<div style="display:flex;align-items:center;gap:10px;background:#161b22;'
                f'border:1px solid #21262d;border-radius:8px;padding:10px 14px;margin-bottom:7px">'
                f'<div style="width:28px;height:28px;background:#fff;border-radius:5px;'
                f'display:flex;align-items:center;justify-content:center;font-size:8px;'
                f'font-weight:700;color:#000;flex-shrink:0">{html.escape(ticker)}</div>'
                f'<div style="font-size:12px;font-weight:700;color:#e6edf3;'
                f'width:150px;flex-shrink:0">{html.escape(name)}</div>'
                f'<div style="flex:1;font-size:11px;color:#8b949e">'
                f'{html.escape(item.get("signal_summary",""))}</div>'
                f'<span style="font-size:9px;font-weight:700;padding:3px 8px;border-radius:10px;'
                f'background:{bg};color:{color};white-space:nowrap">{badge}</span>'
                f'</div>'
            )
        st.markdown(rows, unsafe_allow_html=True)
    else:
        st.markdown(EMPTY_STATE, unsafe_allow_html=True)
