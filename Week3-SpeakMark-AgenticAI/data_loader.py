"""
SpeakMark data loader — Google Sheets edition.

Reads the SpeakMark memory workbook directly from Google Sheets using the
public "gviz" CSV endpoint, which lets us fetch each tab BY NAME (no gid
lookups needed). This requires the sheet to be shared as
"Anyone with the link -> Viewer".

Headers are expected on ROW 1 (title rows were stripped in the Sheets copy).

This module is the only seam between the app and its data source. app.py
calls load_children() exactly as before and does not change.

If the sheet can't be reached (no internet, sharing off, etc.), the loader
falls back to a small inline dataset so the app never crashes during a demo.
"""

import io
import urllib.parse
import urllib.request

import pandas as pd

# Your Google Sheet ID (from the share URL, between /d/ and /edit).
SHEET_ID = "1pAa9Cq7wDI8XhdAfYqLP4-uWiJi2BLZBFsfhUyt1dyg"

# Headers are on row 1 now (title rows stripped). header=0.
HEADER_ROW = 0

RATING_LABELS = {4: "Clear", 3: "Close", 2: "Needs Practice", 1: "Unsure"}


def _tab_url(sheet_name: str) -> str:
    """Build the gviz CSV export URL for a tab, fetched by its name."""
    q = urllib.parse.quote(sheet_name)
    return (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/gviz/tq?tqx=out:csv&sheet={q}"
    )


def _read_tab(sheet_name: str) -> pd.DataFrame:
    """Fetch one tab from Google Sheets as a DataFrame."""
    url = _tab_url(sheet_name)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw), header=HEADER_ROW)
    df = df.dropna(how="all").copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def _trend_from_scores(scores):
    """Classify trend by comparing the recent half to the earlier half."""
    if len(scores) < 4:
        return "stable"
    half = len(scores) // 2
    early = sum(scores[:half]) / half
    late = sum(scores[half:]) / (len(scores) - half)
    if late >= early + 0.4:
        return "improving"
    if late <= early - 0.4:
        return "regressing"
    return "stable"


def load_children() -> dict:
    """Return the children dict the app renders from (read from Google Sheets)."""
    try:
        profile = _read_tab("Child_Profile")
        log = _read_tab("Practice_Log")
        decisions = _read_tab("Agent_Decisions")
        summaries = _read_tab("Weekly_Summaries")
        materials = _read_tab("Therapist_Materials")
    except Exception as exc:  # noqa: BLE001 - any failure -> safe fallback
        print(f"[SpeakMark] Could not read Google Sheet ({exc}); using fallback data.")
        return _fallback_children()

    children = {}
    for _, p in profile.iterrows():
        cid = p["Child_ID"]
        name = p["Child_Name"]
        target = str(p["Target_Sound"]).strip("/")

        child_log = log[log["Child_ID"] == cid].sort_values("Session_ID")
        scores = [
            int(float(s))
            for s in child_log["Practice_Rating_Score"].tolist()
            if str(s).strip() not in ("", "nan", "None")
        ]

        child_dec = decisions[decisions["Child_ID"] == cid].sort_values("Decision_ID")
        latest_dec = child_dec.iloc[-1] if len(child_dec) else None

        child_sum = summaries[summaries["Child_ID"] == cid].sort_values("Summary_ID")
        latest_sum = child_sum.iloc[-1] if len(child_sum) else None

        child_mat = materials[materials["Child_ID"] == cid]
        material_title = child_mat.iloc[-1]["Material_Title"] if len(child_mat) else "—"

        escalation = False
        if latest_sum is not None:
            escalation = str(latest_sum.get("Therapist_Review_Recommended", "No")).strip().lower() in (
                "yes", "true"
            )

        level = str(p["Current_Level"]).strip()
        if "level" not in level.lower():
            level = level + " level"

        children[name] = {
            "age": int(float(p["Age"])),
            "target": target,
            "pattern": p["Primary_Error_Pattern"],
            "level": level,
            "trend": _trend_from_scores(scores),
            "decision": latest_dec["Decision"] if latest_dec is not None else "—",
            "decision_reason": latest_dec["Reason"] if latest_dec is not None else "",
            "escalation": escalation,
            "scores": scores,
            "profile_note": p["Home_Practice_Focus"],
            "material": material_title,
            "summary": latest_sum["Parent_Friendly_Summary"] if latest_sum is not None else "",
            "slp_draft": latest_sum["Possible_SLP_Update_Draft"] if latest_sum is not None else "",
            "recommendation": latest_sum["Practice_Level_Recommendation"] if latest_sum is not None else "",
        }

    return children if children else _fallback_children()


def _fallback_children() -> dict:
    """Minimal inline dataset used only if the sheet can't be reached."""
    return {
        "Ava": {
            "age": 4, "target": "K", "pattern": "Fronting: says /t/ for /k/",
            "level": "Word level", "trend": "improving", "decision": "Keep at word level",
            "decision_reason": "Short /k/ words emerging; not consistent enough to add phrases.",
            "escalation": False, "scores": [2, 2, 3, 2, 3, 3, 3, 4, 3, 4],
            "profile_note": "Short, playful practice works best.",
            "material": "Back /k/ picture cards",
            "summary": "Ava is more consistent on short /k/ words.",
            "slp_draft": "Ava is practicing /k/ at word level — any home cue suggestions?",
            "recommendation": "Continue word-level practice.",
        },
        "Noah": {
            "age": 8, "target": "S", "pattern": "Lateral /s/; blends hard",
            "level": "Reduced to word level", "trend": "regressing",
            "decision": "Reduce difficulty + recommend therapist review",
            "decision_reason": "Declined after prior clear sessions, with frustration.",
            "escalation": True, "scores": [4, 4, 3, 2, 2, 2, 2, 3, 2, 2],
            "profile_note": "Keep practice calm, slow, and short.",
            "material": "/s/ words (reset plan)",
            "summary": "Noah showed a regression this week.",
            "slp_draft": "Noah regressed on /s/ — could you review the home plan?",
            "recommendation": "Reduce to word level; therapist review recommended.",
        },
    }


if __name__ == "__main__":
    kids = load_children()
    print(f"Loaded {len(kids)} children: {list(kids.keys())}")
    for n, c in kids.items():
        print(f"  {n}: trend={c['trend']}, escalation={c['escalation']}, scores={c['scores']}")