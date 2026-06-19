# SpeakMark — AI-Powered Speech Practice Support

SpeakMark helps parents support their child's speech therapy practice between sessions. It uses three specialized AI agents, Google Sheets as persistent memory, n8n for orchestration, and Anthropic Claude for reasoning — all connected through a Streamlit parent-facing app.

> Built as a Week 3 project for the Mastering Agentic AI Bootcamp — The Gen Academy.

---

## What it does

- **Agent 1 — Practice Planning:** Generates an age-appropriate practice plan based on the child's profile, target sound, and session history
- **Agent 2 — Progress Analysis:** Logs each session, reads historical data from Google Sheets, classifies the trend (Improving / Stable / Struggling / Possible Regression), and recommends the next action
- **Agent 3 — Weekly Summary & Escalation:** Reads the full week's sessions and agent decisions, generates a parent-friendly summary, flags if a therapist review is needed, and drafts a therapist update for parent approval

Human-in-the-loop is built in: the parent approves any difficulty change or therapist draft before anything is saved or shared.

---

## Architecture

```
Parent (Streamlit) → n8n Webhook → Google Sheets memory lookup
                                 → Anthropic Claude (claude-sonnet-4-6)
                                 → Agent decision
                                 → Human approval if needed
                                 → Google Sheets write-back
                                 → Streamlit display
```

| Layer | Tool |
|-------|------|
| UI | Streamlit |
| Orchestration | n8n (3 workflows) |
| Memory | Google Sheets (5 tabs) |
| LLM | Anthropic Claude (claude-sonnet-4-6) |

---

## Demo children

Three fake profiles are used to show different agent decisions:

| Child | Age | Target | Pattern |
|-------|-----|--------|---------|
| Ava | 4 | /K/ | Beginner; Needs Practice → Close |
| Emma | 7 | /R/ | Improving; Close → Clear |
| Noah | 8 | /S/ | Regression; Clear → Needs Practice |

---

## Project structure

```
speakmark/
├── app.py                        # Main Streamlit app (5 tabs)
├── data_loader.py                # Demo data loader
├── body.json                     # Sample webhook payload for testing
├── n8n_workflows/
│   ├── agent1_practice_plan.json          # Agent 1 n8n workflow
│   ├── agent2_progress_analysis.json      # Agent 2 n8n workflow
│   ├── agent3_weekly_summary.json         # Agent 3 n8n workflow
│   └── agent3_save_subflow.json           # Agent 3 HITL save sub-flow
└── docs/
    └── SpeakMark_Documentation_v4_final.docx
```

---

## Setup

### Prerequisites
- Python 3.10+
- n8n account (cloud or self-hosted)
- Google account (for Google Sheets)
- Anthropic API key

### 1. Install dependencies

```bash
pip install streamlit requests plotly pandas
```

### 2. Set up Google Sheets

Create a new Google Sheet with these tabs:
- `Child_Profile` — columns: Child_ID, Child_Name, Age, Target_Sound, Current_Level, Therapist_Name, Status
- `Practice_Log` — columns: Session_ID, Child_ID, Child_Name, Date, Practice_Level, Target_Sound, Duration_Minutes, Raw_Parent_Note, Practice_Rating_Score, Practice_Completed, Agent_Decision, Escalation_Flag, HITL_Status
- `Agent_Decisions` — columns: Decision_ID, Child_ID, Date, Agent_Name, Observation, Decision, Reason, Confidence, Human_Approval_Required, Parent_Response, Write_Action, Status
- `Weekly_Summaries` — columns: Summary_ID, Child_Name, Week_Start, Summary_Text, Escalation_Flag, Escalation_Reason, Therapist_Draft, Therapist_Approved, Next_Week_Focus, Generated_Date

Populate with demo data for Ava, Emma, and Noah.

### 3. Set up n8n

1. Import each JSON file from `n8n_workflows/` into n8n (New Workflow → Import from file)
2. On every Google Sheets node, update the Document ID to your Sheet ID
3. On every Anthropic node, attach your Anthropic credential
4. Activate all four workflows

Webhook URLs (replace with your n8n instance):
```
Agent 1: https://YOUR-N8N.app.n8n.cloud/webhook/practice-plan
Agent 2: https://YOUR-N8N.app.n8n.cloud/webhook/progress-analysis
Agent 3: https://YOUR-N8N.app.n8n.cloud/webhook/weekly-summary
Agent 3 save: https://YOUR-N8N.app.n8n.cloud/webhook/weekly-summary/save
```

### 4. Update webhook URLs in app.py

```python
N8N_PLAN_URL     = "https://YOUR-N8N.app.n8n.cloud/webhook/practice-plan"
N8N_PROGRESS_URL = "https://YOUR-N8N.app.n8n.cloud/webhook/progress-analysis"
N8N_SUMMARY_URL  = "https://YOUR-N8N.app.n8n.cloud/webhook/weekly-summary"
```

### 5. Run the app

```bash
streamlit run app.py
```

---

## n8n Workflow overview

### Agent 1 — Practice Plan
`Webhook → Read Child_Profile → Message a Model (Claude) → Respond`
<img width="1361" height="402" alt="image" src="https://github.com/user-attachments/assets/55aed533-de1e-450f-8866-865d1e60fed5" />

### Agent 2 — Progress Analysis
`Webhook → Read Practice_Log + Read Child_Profile → Merge Data → Message a Model (Claude) → Parse Response → Append to Practice_Log + Append to Agent_Decisions → Respond`
<img width="1517" height="367" alt="image" src="https://github.com/user-attachments/assets/b765f575-1c85-4d71-a66f-757e75d4bb4c" />

### Agent 3 — Weekly Summary
`Webhook → Read Practice_Log + Read Agent_Decisions + Read Child_Profile → Merge Data → Message a Model (Claude) → Parse Response → Respond`
<img width="1502" height="571" alt="image" src="https://github.com/user-attachments/assets/9a929a20-60d5-4908-8c3c-fda2afdce30b" />

---

## Human-in-the-loop checkpoints

| Checkpoint | Trigger | Parent options |
|------------|---------|----------------|
| Difficulty change | Agent recommends level up or down | Approve / Keep current / Ask for alternative |
| Therapist review | Regression or escalation detected | Create draft / Not now / Add note |
| Therapist draft approval | Before any summary is shared | Approve / Edit / Discard |

---

## Safety boundaries

- The system does not diagnose speech disorders
- The system does not contact the therapist automatically
- All write actions require parent approval
- Demo uses fake/de-identified data only — no real PHI, no real therapy records

---

## Built with

- [Streamlit](https://streamlit.io)
- [n8n](https://n8n.io)
- [Anthropic Claude](https://anthropic.com)
- [Google Sheets](https://sheets.google.com)
- [Plotly](https://plotly.com)
