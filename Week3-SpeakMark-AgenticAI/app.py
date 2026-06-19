import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
N8N_PLAN_URL = "https://nehmeh.app.n8n.cloud/webhook/practice-plan"
N8N_PROGRESS_URL = "https://nehmeh.app.n8n.cloud/webhook/progress-analysis"
N8N_SUMMARY_URL = "https://nehmeh.app.n8n.cloud/webhook/weekly-summary"

st.set_page_config(
    page_title="SpeakMark",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded",
)



# =====================================================================
# DESIGN SYSTEM
# Identity: "Sound & Speech" — warm, human, credible.
# Display: Fraunces (characterful serif). Body/UI: Inter.
# Trend color is the emotional core, encoded consistently everywhere.
# =====================================================================

INK = "#1E2749"        # deep navy — text + anchor
CORAL = "#FF6B5C"      # brand accent (sound)
PEACH = "#FFA47A"      # brand accent gradient end
CREAM = "#FBF7F2"      # background
CARD = "#FFFFFF"

# Trend system — the one thing a parent should feel before they read.
GREEN = "#2F9E6B"      # improving
GREEN_BG = "#E7F5EE"
AMBER = "#E8943A"      # stable / watch
AMBER_BG = "#FBF0E2"
CLAY = "#D85A4A"       # regressing / escalation
CLAY_BG = "#FBE8E4"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', system-ui, sans-serif;
        color: {INK};
    }}
    .stApp {{ background-color: {CREAM}; }}

    h1, h2, h3, h4 {{
        font-family: 'Fraunces', Georgia, serif !important;
        color: {INK};
        letter-spacing: -0.01em;
    }}

    /* ---- Hero ---- */
    .hero {{
        position: relative;
        padding: 34px 36px;
        border-radius: 22px;
        background: linear-gradient(125deg, {INK} 0%, #2C3A63 55%, #3B4D7E 100%);
        color: #fff;
        margin-bottom: 22px;
        overflow: hidden;
    }}
    .hero-eyebrow {{
        font-size: 13px; font-weight: 600; letter-spacing: 0.14em;
        text-transform: uppercase; color: {PEACH}; margin-bottom: 8px;
    }}
    .hero-title {{
        font-family: 'Fraunces', serif; font-size: 46px; font-weight: 600;
        line-height: 1.02; margin: 0 0 10px 0; color: #fff;
    }}
    .hero-sub {{ font-size: 17px; max-width: 560px; opacity: 0.9; line-height: 1.5; }}
    .hero-wave {{
        position: absolute; right: -10px; top: 0; height: 100%; width: 320px;
        opacity: 0.16; display: flex; align-items: center; gap: 7px; padding-right: 30px;
        justify-content: flex-end;
    }}
    .hero-wave span {{
        display: block; width: 7px; border-radius: 6px; background: {PEACH};
    }}

    /* ---- Phoneme medallion (the signature element) ---- */
    .phoneme {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 78px; height: 78px; border-radius: 20px;
        background: linear-gradient(135deg, {CORAL} 0%, {PEACH} 100%);
        font-family: 'Fraunces', serif; font-size: 34px; font-weight: 600;
        color: #fff; box-shadow: 0 8px 20px rgba(255,107,92,0.28);
    }}

    /* ---- Cards ---- */
    .card {{
        padding: 22px 24px; border-radius: 18px; background: {CARD};
        border: 1px solid #EFE9E1; box-shadow: 0 6px 20px rgba(30,39,73,0.05);
        margin-bottom: 16px;
    }}
    .card h3 {{ margin-top: 4px; }}

    .eyebrow {{
        font-size: 12px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: {CORAL};
    }}
    .muted {{ color: #6B7280; font-size: 14px; line-height: 1.55; }}

    /* ---- Trend chips (consistent everywhere) ---- */
    .trend {{
        display: inline-flex; align-items: center; gap: 7px;
        padding: 6px 13px; border-radius: 999px; font-weight: 700; font-size: 13px;
    }}
    .trend .dot {{ width: 9px; height: 9px; border-radius: 50%; }}
    .t-up   {{ background: {GREEN_BG}; color: {GREEN}; }}
    .t-up .dot   {{ background: {GREEN}; }}
    .t-flat {{ background: {AMBER_BG}; color: {AMBER}; }}
    .t-flat .dot {{ background: {AMBER}; }}
    .t-down {{ background: {CLAY_BG}; color: {CLAY}; }}
    .t-down .dot {{ background: {CLAY}; }}

    /* ---- Approval (the HITL moment) ---- */
    .approval {{
        padding: 22px 24px; border-radius: 18px; background: {CLAY_BG};
        border: 1.5px solid {CLAY}; margin-bottom: 16px;
    }}
    .approval .label {{
        font-size: 12px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: {CLAY};
    }}
    .draft {{
        background: #fff; border-radius: 14px; padding: 18px 20px;
        border: 1px solid #F0D9D4; margin-top: 12px; font-size: 15px; line-height: 1.6;
        color: {INK};
    }}
    .draft-meta {{ font-size: 12px; color: #9A8F88; margin-bottom: 8px;
        text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }}

    /* ---- Stat row ---- */
    .stat {{
        background: {CARD}; border: 1px solid #EFE9E1; border-radius: 16px;
        padding: 16px 18px; box-shadow: 0 4px 14px rgba(30,39,73,0.04);
    }}
    .stat .k {{ font-size: 12px; font-weight: 600; letter-spacing: 0.06em;
        text-transform: uppercase; color: #8A8078; }}
    .stat .v {{ font-family: 'Fraunces', serif; font-size: 27px; font-weight: 600;
        color: {INK}; margin-top: 3px; }}

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {{ background: #fff; border-right: 1px solid #EFE9E1; }}
    .tool {{
        padding: 12px 14px; border-radius: 13px; background: {CREAM};
        border: 1px solid #EFE9E1; margin-bottom: 9px;
    }}
    .tool .tt {{ font-weight: 700; font-size: 14px; margin-bottom: 2px; color: {INK}; }}
    .tool .td {{ font-size: 12.5px; color: #6B7280; line-height: 1.4; }}

    /* tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{
        font-weight: 600; font-size: 14px; padding: 8px 14px; border-radius: 10px;
    }}
    .stTabs [aria-selected="true"] {{ background: {CORAL}1A; color: {CORAL}; }}

    .stButton button {{ border-radius: 11px; font-weight: 600; }}

    /* ---- Top approval alert (always visible) ---- */
    @keyframes pulseGlow {{
        0%   {{ box-shadow: 0 0 0 0 rgba(216,90,74,0.30); }}
        70%  {{ box-shadow: 0 0 0 12px rgba(216,90,74,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(216,90,74,0); }}
    }}
    .alert-bar {{
        display: flex; align-items: center; gap: 14px;
        padding: 15px 20px; border-radius: 15px;
        background: {CLAY_BG}; border: 1.5px solid {CLAY};
        margin-bottom: 18px; animation: pulseGlow 2.4s infinite;
    }}
    .alert-icon {{
        flex: none; width: 38px; height: 38px; border-radius: 11px;
        background: {CLAY}; color: #fff; font-size: 19px;
        display: flex; align-items: center; justify-content: center;
    }}
    .alert-text {{ flex: 1; color: #7A4036; }}
    .alert-text .at-title {{ font-weight: 700; color: {CLAY}; font-size: 15px; }}
    .alert-text .at-sub {{ font-size: 13.5px; opacity: 0.9; }}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# DATA  — loaded from the SpeakMark workbook via data_loader.
# This is the single seam to the data source. To switch to Google Sheets
# later, only data_loader.load_children() changes; the app stays the same.
# Scores use the project scale: Clear=4, Close=3, Needs Practice=2, Unsure=1
# =====================================================================

from data_loader import load_children, RATING_LABELS

children = load_children()

TREND_META = {
    "improving": ("t-up", "Improving", GREEN),
    "stable":    ("t-flat", "Stable", AMBER),
    "regressing":("t-down", "Regressing", CLAY),
}

def trend_chip(trend_key):
    cls, label, _ = TREND_META[trend_key]
    return f'<span class="trend {cls}"><span class="dot"></span>{label}</span>'

# =====================================================================
# HERO
# =====================================================================
wave_bars = "".join(
    f'<span style="height:{h}px"></span>'
    for h in [22, 40, 64, 34, 78, 30, 54, 44, 70, 26, 48, 36]
)
st.markdown(f"""
<div class="hero">
    <div class="hero-wave">{wave_bars}</div>
    <div class="hero-eyebrow">Home practice companion</div>
    <div class="hero-title">SpeakMark</div>
    <div class="hero-sub">
        Keep track of speech practice between therapy sessions — and know when it's
        time to loop in your therapist.
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# SIDEBAR
# =====================================================================
st.sidebar.markdown(f"<h3 style='margin-bottom:0'>🗣️ SpeakMark</h3>", unsafe_allow_html=True)
st.sidebar.caption("Sample data")

selected_child = st.sidebar.selectbox("Whose practice?", list(children.keys()))
child = children[selected_child]
cls, trend_label, trend_color = TREND_META[child["trend"]]

st.sidebar.markdown("---")
st.sidebar.markdown("**Snapshot**")
st.sidebar.markdown(
    f"<div class='muted'>Age {child['age']} · target /{child['target']}/<br>"
    f"{child['level']}</div>", unsafe_allow_html=True)
st.sidebar.markdown(f"<div style='margin-top:8px'>{trend_chip(child['trend'])}</div>",
                    unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Practice toolkit**")
st.sidebar.caption("Reminders parents can use mid-practice.")
for tt, td in [
    ("🐢 Slow down", "Use a slower rate before retrying a tricky word."),
    ("🌬️ Big breath", "Take a full breath before a word or sentence."),
    ("➰ Stretch the sound", "Stretch the target sound so the child can hear and feel it."),
    ("⏸️ Pause & reset", "Pause when frustrated, reset, then try again."),
]:
    st.sidebar.markdown(
        f"<div class='tool'><div class='tt'>{tt}</div><div class='td'>{td}</div></div>",
        unsafe_allow_html=True)

# =====================================================================
# IDENTITY STRIP — phoneme medallion + stats
# =====================================================================
left, right = st.columns([1, 3.4])
with left:
    st.markdown(f"<div class='phoneme'>/{child['target']}/</div>", unsafe_allow_html=True)
with right:
    avg = round(sum(child["scores"]) / len(child["scores"]), 1)
    avg_word = RATING_LABELS[round(avg)]
    recent = child["scores"][-1]
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='stat'><div class='k'>This week's trend</div>"
                f"<div class='v' style='color:{trend_color}'>{trend_label}</div></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div class='stat'><div class='k'>Recent clarity</div>"
                f"<div class='v'>{RATING_LABELS[recent]}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat'><div class='k'>Avg this period</div>"
                f"<div class='v'>{avg_word} <span style='font-size:15px;color:#9A8F88'>· {avg}/4</span></div></div>",
                unsafe_allow_html=True)

st.write("")

# =====================================================================
# TOP ALERT — always visible when an approval is pending, on any tab.
# Streamlit renders top-to-bottom, so the actual buttons live at the top
# of the Weekly summary tab; this banner announces the ask on page load.
# =====================================================================
pending = (
    child["escalation"]
    and st.session_state.get(f"approval_{selected_child}") in (None, "edit")
)
if pending:
    st.markdown(f"""
    <div class="alert-bar">
        <div class="alert-icon">🔔</div>
        <div class="alert-text">
            <div class="at-title">SpeakMark is asking for your approval</div>
            <div class="at-sub">{selected_child} had a regression this week — a therapist update is
            drafted and waiting. Open the <b>Weekly summary</b> tab to review and decide.
            Nothing is shared until you approve it.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================================
# TABS
# =====================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Child profile", "Practice plan", "Log practice", "Progress", "Weekly summary"
])

# ---- Tab 1: Profile ----
with tab1:
    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Profile</div>
        <h3>{selected_child} · age {child['age']}</h3>
        <p class="muted">
            <b>Target sound:</b> /{child['target']}/<br>
            <b>What we're hearing:</b> {child['pattern']}<br>
            <b>Current level:</b> {child['level']}<br>
            <b>Therapist material:</b> {child['material']}
        </p>
        <p class="muted" style="margin-top:10px">{child['profile_note']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Why this matters</div>
        <h3>The home-to-therapy feedback loop</h3>
        <p class="muted">
            What happens during home practice is usually invisible by the next therapy
            session. SpeakMark captures it while it's fresh, tracks how each sound is
            trending, and turns it into a short, parent-approved update your therapist
            can actually use.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ---- Tab 2: Plan ----
with tab2:
    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Practice planning agent</div>
        <h3>Today's recommended practice</h3>
        <p class="muted">A plan shaped to {selected_child}'s age, target sound, and recent sessions.
        In the full system this is generated through n8n and the reasoning model from Google Sheets memory.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Generate practice plan", type="primary"):
        try:
            resp = requests.post(N8N_PLAN_URL, json={"child": selected_child}, timeout=20)
            data = resp.json()
            st.markdown(f"""
            <div class="card" style="border-left:4px solid {CORAL}">
                <div class="eyebrow">Plan for {selected_child}</div>
                <p class="muted">{data.get('plan', 'No plan returned')}</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not reach the plan service: {e}")
        plans = {
            "Ava": dict(level="Word level", items="cat, cup, key, cow, cookie",
                idea="Hide the picture cards around the room; say each word 3 times when found.",
                tip="Keep it to 5–7 minutes. Use the mirror so Ava can see the back-of-tongue sound.",
                why="Ava is young and is doing best with short, playful repetition."),
            "Emma": dict(level="Sentence level", items="The red rabbit ran. · I see a red car. · The robot rolls.",
                idea="Read each sentence slowly, then use it in a silly made-up story.",
                tip="Slow the first sound, then say the whole sentence smoothly. Repeat her clearest tries.",
                why="Emma has improved with initial /r/ and is ready for short sentences."),
            "Noah": dict(level="Word level (reduced)", items="sun, see, sip, soup, seal",
                idea="One word at a time, with a calm pause after each attempt. Add 'see sun' only if relaxed.",
                tip="Use relaxed airflow. Stop after 5–7 minutes. Don't repeat until frustrated.",
                why="Noah shows a recent regression, so we're rebuilding confidence at a simpler level."),
        }
        p = plans[selected_child]
        st.markdown(f"""
        <div class="card" style="border-left:4px solid {CORAL}">
            <div class="eyebrow">Plan for {selected_child}</div>
            <h3>{p['level']}</h3>
            <p class="muted"><b>Practice items:</b> {p['items']}<br>
            <b>Try this:</b> {p['idea']}<br>
            <b>Parent tip:</b> {p['tip']}<br>
            <b>Why this plan:</b> {p['why']}</p>
        </div>
        """, unsafe_allow_html=True)
        if child["escalation"] or child["level"].lower().startswith("reduced"):
            st.info("This plan changes the practice level — you'll be asked to approve it before it's saved.")

# ---- Tab 3: Log ----
with tab3:
    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Parent input</div>
        <h3>Log a practice session</h3>
        <p class="muted">Type your notes, or dictate them with a voice-to-text tool and paste the
        text here. You review the note before it's saved — SpeakMark never stores audio.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    completed = c1.selectbox("Practice completed?", ["Yes", "No"])
    rating = c2.selectbox("How did it sound?", ["Clear", "Close", "Needs Practice", "Unsure"])
    words = st.text_input("Words or sounds practiced")
    strategy_used = st.multiselect("Strategies used",
        ["Slow down", "Big breath", "Stretch the sound", "Pause & reset", "None"])
    c3, c4 = st.columns(2)
    voice_used = c3.selectbox("Used voice-to-text?", ["No", "Yes"])
    reviewed = c4.checkbox("I reviewed this note", value=True)
    note = st.text_area("Your observation",
        placeholder="e.g. Key was clearer today. Cow still sounded like 'tow'. Stayed engaged for 5 minutes.")

    if st.button("Save session", type="primary"):
        if not reviewed:
            st.warning("Please review the note before saving.")
        else:
            rating_map = {"Clear": 4, "Close": 3, "Needs Practice": 2, "Unsure": 1}
            try:
                resp = requests.post(N8N_PROGRESS_URL, json={
                    "child":        selected_child,
                    "session_date": str(pd.Timestamp.today().date()),
                    "duration_mins": 15,
                    "difficulty":   child["level"],
                    "accuracy_pct": rating_map[rating],
                    "target_sounds": f"/{child['target']}/",
                    "notes":        note or "No note provided"
                }, timeout=25)
                data = resp.json()
                st.success("Session saved and analysed.")
                st.markdown(f"""
                <div class="card">
                    <div class="eyebrow">Structured observation</div>
                    <p class="muted">
                    <b>Practiced:</b> {words or '—'}<br>
                    <b>Sounded:</b> {rating}<br>
                    <b>Strategies:</b> {', '.join(strategy_used) if strategy_used else 'None'}<br>
                    <b>Note:</b> {note or '—'}<br><br>
                    <b>Agent decision:</b> {data.get('recommendation', '—')}<br>
                    <b>Trend:</b> {data.get('trend', '—')}<br>
                    <b>Analysis:</b> {data.get('analysis', '—')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not reach the progress service: {e}")

# ---- Tab 4: Progress ----
with tab4:
    scores = child["scores"]
    sessions = [f"S{i+1}" for i in range(len(scores))]
    line_color = trend_color

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sessions, y=scores, mode="lines+markers",
        line=dict(color=line_color, width=3, shape="spline"),
        marker=dict(size=10, color=line_color, line=dict(color="#fff", width=2)),
        hovertemplate="%{x}: %{customdata}<extra></extra>",
        customdata=[RATING_LABELS[s] for s in scores],
    ))
    fig.update_layout(
        height=340, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(
            range=[0.7, 4.3], tickmode="array",
            tickvals=[1, 2, 3, 4],
            ticktext=["Unsure", "Needs<br>Practice", "Close", "Clear"],
            gridcolor="#F0EAE2",
        ),
        xaxis=dict(showgrid=False),
        font=dict(family="Inter", color=INK, size=13),
    )
    st.markdown(f"<div class='eyebrow'>Progress · /{child['target']}/ clarity over sessions</div>",
                unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    cA, cB = st.columns(2)
    with cA:
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Progress analysis agent</div>
            <div style="margin:6px 0 10px 0">{trend_chip(child['trend'])}</div>
            <h3 style="margin-top:0">{child['decision']}</h3>
            <p class="muted">{child['decision_reason']}</p>
        </div>
        """, unsafe_allow_html=True)
    with cB:
        if child["escalation"]:
            st.markdown(f"""
            <div class="card" style="border:1.5px solid {CLAY}; background:{CLAY_BG}">
                <div class="eyebrow" style="color:{CLAY}">Human review needed</div>
                <h3 style="margin-top:6px; color:{CLAY}">Therapist review recommended</h3>
                <p class="muted" style="color:#7A4036">Nothing is shared automatically. You decide whether
                to send an update — see the Weekly summary tab to review and approve the draft.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="card" style="border:1.5px solid {GREEN}33; background:{GREEN_BG}">
                <div class="eyebrow" style="color:{GREEN}">On track</div>
                <h3 style="margin-top:6px; color:{GREEN}">Keep going</h3>
                <p class="muted" style="color:#2C6A4E">Continue the current plan and keep logging.
                SpeakMark will flag it here if the trend changes.</p>
            </div>
            """, unsafe_allow_html=True)

# ---- Tab 5: Weekly summary (the HITL moment) ----
with tab5:
    # Generate summary from Agent 3
    skey = f"summary_{selected_child}"
    if skey not in st.session_state:
        st.session_state[skey] = None

    if st.button("Generate weekly summary", type="primary"):
        with st.spinner("Agent 3 is analysing this week's sessions..."):
            try:
                resp = requests.post(N8N_SUMMARY_URL, json={
                    "child": selected_child,
                    "week_start": "2026-06-13",
                    "include_therapist": True
                }, timeout=30)
                st.session_state[skey] = resp.json()
            except Exception as e:
                st.error(f"Could not reach summary service: {e}")

    data = st.session_state[skey]

    if data:
        # Show summary card
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Summary &amp; escalation agent</div>
            <h3>This week, in plain language</h3>
            <p class="muted">{data.get('summary', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Show next week focus
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Recommended next step</div>
            <p class="muted" style="margin-top:6px">{data.get('next_week_focus', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        # HITL — escalation approval
        if data.get('escalation_flag'):
            akey = f"approval_{selected_child}"
            if akey not in st.session_state:
                st.session_state[akey] = None

            if st.session_state[akey] is None:
                st.markdown(f"""
                <div class="approval">
                    <div class="label">⚠ Pending your approval</div>
                    <h3 style="margin:6px 0 2px 0; color:{CLAY}">Share an update with the therapist?</h3>
                    <p class="muted" style="color:#7A4036; margin-bottom:4px">
                        {data.get('escalation_reason', '')}
                        Here's the draft — nothing is sent until you approve it.
                    </p>
                    <div class="draft">
                        <div class="draft-meta">Draft update · {selected_child}</div>
                        {data.get('therapist_draft', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                b1, b2, b3 = st.columns([1, 1, 1])
                if b1.button("Approve & prepare update", type="primary"):
                    st.session_state[akey] = "approved"
                    st.rerun()
                if b2.button("Edit draft"):
                    st.session_state[akey] = "edit"
                    st.rerun()
                if b3.button("Not now"):
                    st.session_state[akey] = "declined"
                    st.rerun()

            elif st.session_state[akey] == "approved":
                st.markdown(f"""
                <div class="card" style="border:1.5px solid {GREEN}; background:{GREEN_BG}">
                    <div class="eyebrow" style="color:{GREEN}">✓ Approved</div>
                    <h3 style="margin-top:6px; color:{GREEN}">Update ready to share</h3>
                    <p class="muted" style="color:#2C6A4E">You approved the therapist update.
                    SpeakMark didn't contact anyone on its own.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("← Back to pending"):
                    st.session_state[akey] = None
                    st.rerun()

            elif st.session_state[akey] == "edit":
                edited = st.text_area("Edit the draft before approving",
                    value=data.get('therapist_draft', ''), height=120)
                if st.button("Approve edited update", type="primary"):
                    st.session_state[akey] = "approved"
                    st.rerun()
                if st.button("← Back"):
                    st.session_state[akey] = None
                    st.rerun()

            else:
                st.markdown(f"""
                <div class="card">
                    <div class="eyebrow">Saved for later</div>
                    <p class="muted" style="margin-top:6px">No update was shared.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("← Back to pending"):
                    st.session_state[akey] = None
                    st.rerun()
        else:
            st.markdown(f"""
            <div class="card" style="border:1.5px solid {GREEN}33; background:{GREEN_BG}">
                <div class="eyebrow" style="color:{GREEN}">No therapist review needed</div>
                <p class="muted" style="color:#2C6A4E; margin-top:6px">
                    {selected_child}'s practice is on track this week.
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Weekly summary</div>
            <p class="muted" style="margin-top:6px">Click "Generate weekly summary" to analyse
            this week's sessions and get a parent-friendly summary.</p>
        </div>
        """, unsafe_allow_html=True)