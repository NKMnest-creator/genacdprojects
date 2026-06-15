# 🏏 ⚽ 🏉 Sports Knowledge RAG

A retrieval-augmented Q&A app covering **Cricket, Soccer, and Rugby** — rules, history,
and World Cup records — built for the Gen Academy Week 2 RAG project.

> *My RAG app helps curious sports fans answer questions about rules, history,
> players, and World Cup records from 8 Wikipedia-sourced PDFs (Cricket, Soccer,
> Rugby — 479 chunks) in a chat interface, with ≥85% faithfulness and <10s
> response time.*

---

## What this is

Ask it things like *"How many times has Brazil won the World Cup?"* or *"What
are the rules for leg before wicket in cricket?"* and it retrieves the relevant
passages from the source documents, cites them, and answers — or honestly says
**"I could not find this in the available sources"** if the answer isn't there.

An **agentic router** classifies each question (rules / history / comparison /
cross-sport / out-of-scope) and decides which sport's knowledge base(s) to
search — including running three separate searches with rewritten,
sport-specific queries for cross-sport questions.

---

## Architecture

```
User question (Streamlit chat)
        │
        ▼
  Query Router (Claude Haiku, temperature=0)
   ├─ classifies: rules / history / comparison / cross_sport / out_of_scope
   └─ for cross_sport: rewrites the question per sport
        │
        ▼
  Filtered Retrieval (ChromaDB, metadata filter on `sport`)
   ├─ single-sport categories → 1 filtered search
   ├─ cross_sport → 3 filtered searches (one per sport, rewritten query)
   └─ out_of_scope → skipped entirely (no embedding call)
        │
        ▼
  Synthesis (Claude Haiku, temperature=0)
   ├─ answers ONLY from retrieved chunks, with inline citations
   └─ says "I could not find this" if context is insufficient
        │
        ▼
  Response Cache (query_cache.json — skips router+synthesis on repeat questions)
        │
        ▼
  Streamlit UI — answer + expandable "Sources" + "How this was answered" panel
```

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Framework | LlamaIndex | Document loaders, chunking, retrievers, vector store integration |
| Embeddings | Nebius Token Factory — `Qwen/Qwen3-Embedding-8B` (4096-dim) | Satisfies the project's required Nebius model call |
| Vector store | ChromaDB (local, persistent) | Zero cost, no account/API key, runs entirely offline |
| LLM (router + synthesis) | Claude Haiku 4.5, `temperature=0` | Cheapest/fastest tier; deterministic for consistency |
| UI | Streamlit | Chat interface with source citations and routing transparency |

---

## Corpus

**8 PDFs, 196 pages → 479 chunks** (SentenceSplitter, chunk_size=512, overlap=50):

- **cricket/**: rules.pdf, history.pdf, records.pdf
- **soccer/**: rules.pdf, history.pdf, records.pdf
- **rugby/**: rules.pdf, history.pdf

Sourced from Wikipedia "Laws of..." and "World Cup" pages — chosen over official
rulebooks (MCC Laws, FIFA Laws of the Game) because the official PDFs run
100+ pages of diagrams/legal formatting that extracts messily, vs. Wikipedia's
clean ~10-20 page format. **This is a static snapshot, not live-synced** — see
Known Limitations.

Each chunk is tagged with `sport` and `content_type` (rules/history/records),
derived automatically from the folder/filename — this metadata powers the
router's filtered retrieval.

---

## Setup

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   ```
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your real keys:
   ```
   ANTHROPIC_API_KEY=...
   NEBIUS_API_KEY=...
   ```

4. Sanity check:
   ```
   python test_connection.py
   ```
   Should print `connection successful`.

5. The ChromaDB index (`chroma_db/`) is built by running `sports_rag.ipynb`
   end-to-end (Steps 1-4). It's not checked into the repo (see `.gitignore`) —
   rebuild it from `sports_docs/` if starting fresh.

6. Run the app:
   ```
   streamlit run app.py
   ```

---

## Example Q&A

*(Sources for each answer are shown separately in the app's expandable
"Sources" panel — citations are intentionally kept out of the answer text
itself for readability.)*

**1. "How many times has Brazil won the World Cup?"** *(history → soccer)*
> Brazil has won the FIFA World Cup **5 times**. They are the most successful
> World Cup team in history and are also the only nation to have played in
> every World Cup tournament to date. Brazil won their titles in 1958, 1962,
> 1970, 1994, and 2002.
>
> *Sources: soccer / history, page 12; soccer / records, page 21 (×2)*

**2. "What are the rules for leg before wicket in cricket?"** *(rules → cricket)*
> A batter is out leg before wicket if: (1) the ball hits the batter's body
> without first hitting the bat, (2) the ball would have hit the wicket if the
> batter had not been in the way, and (3) the ball did not pitch on the leg
> side — **unless** the ball strikes outside the line of off-stump while the
> batter is attempting to play a stroke, in which case they are not out.
>
> *Sources: cricket / rules, pages 13, 11, 15*

**3. "How many wickets did Shane Bond take in the 2007 World Cup?"** *(history → cricket — refusal + adjacent fact)*
> I could not find this in the available sources. The retrieved chunks contain
> information about Glenn McGrath taking 26 wickets at the 2007 World Cup, but
> they do not include any information about Shane Bond's wicket tally in that
> tournament.
>
> *Sources: cricket / records, pages 20, 24, 22*

**4. "Which country dominates the most sports at World Cup level?"** *(cross_sport → cricket + soccer + rugby, with rewritten sub-queries)*
> **Cricket:** Australia dominates with 6 World Cup titles (1987-2023), more
> than any other nation. **Soccer:** Brazil dominates with 5 titles and is the
> only nation to have played in every World Cup. **Rugby:** South Africa leads
> with 4 titles, followed by New Zealand with 3. **Overall:** No single country
> dominates across all three — each leads its own sport.
>
> *Sources: 3 chunks per sport (9 total) — one rewritten sub-query per sport*

**5. "When is the next Cricket World Cup?" / "When was the last Rugby World Cup?" / "What year was the latest soccer World Cup?"** *(single-sport history — non-deterministic, see Known Limitations)*
> *Sometimes (correct):* "The next Cricket World Cup will be in 2027, with 14
> teams" / "South Africa won the latest Rugby World Cup in 2023, defeating New
> Zealand" / "The most recent FIFA World Cup was held in 2022 in Qatar, won by
> Argentina."
>
> *Sometimes (refusal):* "I could not find this in the available sources" —
> reproduced for all three sports. The fact is always present in the index
> (a Wikipedia infobox field, e.g. "Holders: South Africa (2023)"), but raw
> "next/last/latest" phrasing doesn't always retrieve that chunk into the
> top-k — see Known Limitations for the root cause and proposed fix.

---

## RAG vs. Plain-LLM Eval (required deliverable)

Ran 5 questions through both the RAG pipeline and a plain Claude Haiku call
(no retrieval), twice each at `temperature=0`. Full results in
`eval_results.json`.

| Question | RAG | Plain-LLM |
|---|---|---|
| Brazil WC wins | Correct (5), cited | Correct (5), with years |
| LBW rules | Correct exception clause, cited | Exception clause **logically inverted**, both runs |
| Messi vs Ronaldo | Honest refusal, identical both runs | Confident, but appearance count contradicts itself (7 vs 5) across runs |
| Cross-sport dominance | Per-sport breakdown, honest "no single winner" | Pulls in volleyball/futsal/France — outside corpus scope |
| Shane Bond wickets | Honest refusal + correct adjacent fact (McGrath, 26, cited) | Confident, specific, **fabricated** (13 wickets, false "run to the final") |

**Finding:** across all 5 questions, RAG never stated a false fact. Plain-LLM
was correct on 1, subtly wrong on 1, self-contradictory on 1, scope-drifted on
1, and fabricated on 1. RAG's "I don't know" path costs some helpfulness but
buys reliability — and crucially, every RAG claim is independently checkable
via its citation.

---

## The agentic layer

The router (Claude Haiku, `temperature=0`) does two things beyond simple
classification:

1. **Scopes retrieval** — for single-sport questions, it filters ChromaDB to
   only that sport's chunks (e.g., a cricket rules question never sees soccer
   chunks, even if vocabulary overlaps).
2. **Rewrites cross-sport queries** — "Which country dominates the most sports
   at World Cup level?" becomes three separate, sport-specific queries (e.g.
   *"Which country has won the most Cricket World Cups?"*), each run against
   that sport's filtered index. This was necessary because the raw question,
   searched globally, returned soccer-only results — and even searched against
   the cricket-only index, scored a citations page far higher than the actual
   winners table.

Out-of-scope questions (different sports, weather, general trivia) are
detected before any retrieval or synthesis call — zero wasted API calls.

---

## Known limitations

- **Citation noise**: Wikipedia bibliography/reference-list chunks sometimes
  score competitively on vocabulary overlap despite containing no answer
  content (e.g., a "Brazil World Cup Wins" article *title* in a references list
  scoring near a real World Cup results table). The synthesis prompt explicitly
  tells Claude to distinguish citation noise from citation *titles that state a
  fact* — but the distinction is a judgment call, not a hard filter.

- **Infobox-style chunks**: Wikipedia infoboxes are compressed label-value text
  ("Holders South Africa (2023) Most titles..."), not prose. Early on, Claude
  treated connecting these fields into an answer as "guessing." Fixed via an
  explicit synthesis rule, but this is a recurring pattern across all 8 PDFs.

- **Retrieval non-determinism near the top-k cutoff, for "latest/next" questions**:
  Nebius's embedding API isn't perfectly bit-reproducible call-to-call. For
  "next Cricket World Cup", "last Rugby World Cup", and "latest soccer World
  Cup" — one question per sport, all three tested — the correct answer lives in
  a Wikipedia infobox field (e.g. "Holders: South Africa (2023)" or "Upcoming
  tournament: 2027"). That chunk and several citation/reference chunks score
  within ~0.02-0.03 of each other, so the correct chunk can fall in or out of
  the top-k depending on the run — causing the *same question* to sometimes
  succeed and sometimes return "I could not find this" (see Example 5 above).
  Bumping `top_k` from 3 to 5 did not reliably fix this for the rugby case.

  **Root cause and fix identified**: cross-sport questions already solve this
  via per-sport query *rewriting* — "dominates the most sports" gets rewritten
  to "Which country has won the most Cricket/Soccer/Rugby World Cups?" per
  sport, which reliably retrieves the right infobox chunk (proven working,
  Example 4). The fix is to extend this rewriting to single-sport categories
  too, using canonical/encyclopedic phrasing ("most recent", "current holders")
  instead of colloquial phrasing ("next", "last"). A first attempt at
  generalizing the router prompt to produce `sub_queries` for all categories
  was prototyped, but Haiku did not reliably populate `sub_queries` for
  `history`/`rules`/`comparison` categories the way it does for `cross_sport`
  (which has a worked example in the prompt) — would need additional
  per-category examples and another testing pass. Reverted to the stable
  cross-sport-only version for submission; this is the top item for future
  work.

- **Static corpus**: the index is a one-time snapshot of Wikipedia at build
  time. "Latest"/"next" questions are bounded by that snapshot date — there's
  no refresh pipeline.

- **Genuine corpus gaps**: some facts (e.g., individual match "Man of the
  Match" awards) likely aren't in the source pages at all — Wikipedia's
  "history" pages cover tournament-level summaries, not per-match trivia. RAG
  correctly refuses rather than guessing, but this is a coverage gap, not a
  retrieval bug.

- **Cache is global, not per-user**: `query_cache.json` is a single shared
  file — fine for a class demo (everyone benefits from cache hits), but
  wouldn't scale to multi-tenant production without per-user/TTL logic.

---

## Project structure

```
sports_rag/
├── sports_docs/
│   ├── cricket/  (rules.pdf, history.pdf, records.pdf)
│   ├── soccer/   (rules.pdf, history.pdf, records.pdf)
│   └── rugby/    (rules.pdf, history.pdf)
├── sports_rag.ipynb     # build + test pipeline (Steps 1-9)
├── app.py               # Streamlit chat app (Step 10)
├── query_cache.json      # response cache (Step 8)
├── eval_results.json     # RAG vs plain-LLM eval (Step 9)
├── requirements.txt
├── .env.example
├── test_connection.py
└── README.md
```
