import os
import re
import json
import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic
import chromadb

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.nebius import NebiusEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

load_dotenv(override=True)

CACHE_FILE = "query_cache.json"

st.set_page_config(page_title="Sports Knowledge RAG", page_icon="🏆", layout="wide")

# ---------------------------------------------------------------------------
# Pipeline setup (cached so it only runs once per server session)
# ---------------------------------------------------------------------------

@st.cache_resource
def load_pipeline():
    embed_model = NebiusEmbedding(
        model_name="Qwen/Qwen3-Embedding-8B",
        api_key=os.environ["NEBIUS_API_KEY"],
        api_base="https://api.tokenfactory.nebius.com/v1",
    )
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection("sports_rag")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    claude_client = Anthropic()
    return index, claude_client, collection


index, claude_client, collection = load_pipeline()

# ---------------------------------------------------------------------------
# Prompts (same as the notebook's final versions)
# ---------------------------------------------------------------------------

ROUTER_SYSTEM_PROMPT = """You are a query router for a sports knowledge RAG system covering Cricket, Soccer, and Rugby ONLY.

Given a user question, classify it and decide which sport(s) knowledge base(s) to search.

Categories:
- "rules": questions about how the game is played, laws, regulations, equipment
- "history": questions about World Cup results, historical events, records, statistics
- "comparison": questions comparing players, teams, or stats (within one sport)
- "cross_sport": questions that require comparing or combining information ACROSS cricket, soccer, and rugby
- "out_of_scope": the question is about a DIFFERENT sport (baseball, basketball, tennis, etc.) or unrelated to sports entirely (weather, general knowledge)

IMPORTANT: This system only covers cricket, soccer, and rugby. If a question asks something like "which sport" or "across sports" or "dominates the most sports" WITHOUT naming a specific sport outside this system's coverage, treat it as "cross_sport" -- interpret "sports" as referring to cricket, soccer, and rugby (the sports this system has), not sports in general.

For "cross_sport" questions ONLY, also produce a "sub_queries" object: for each of cricket, soccer, rugby, write a focused, sport-specific reformulation of the question that would retrieve the most relevant chunk for THAT sport (e.g. a "World Cup winners" question becomes "Which country has won the most Cricket World Cups?" / "...Soccer World Cups?" / "...Rugby World Cup titles?"). For all other categories, omit "sub_queries" or set it to {}.

Respond with ONLY a JSON object, nothing else -- no markdown code fences, no explanation, no backticks.
Format: {"category": "...", "sports": [...], "sub_queries": {"cricket": "...", "soccer": "...", "rugby": "..."}}

Example: "Which country dominates the most sports at World Cup level?" -> {"category": "cross_sport", "sports": ["cricket", "soccer", "rugby"], "sub_queries": {"cricket": "Which country has won the most Cricket World Cups?", "soccer": "Which country has won the most Soccer World Cups?", "rugby": "Which country has won the most Rugby World Cup titles?"}}

For "rules", "history", and "comparison", "sports" should contain ONLY the relevant sport(s) -- usually just one.
For "cross_sport", "sports" should always be ["cricket", "soccer", "rugby"].
For "out_of_scope", "sports" should be [].
If a question doesn't name a sport but the category is rules/history/comparison, infer it from context (player names, terminology, etc.)."""

SYNTHESIS_SYSTEM_PROMPT = '''You are a sports knowledge assistant covering Cricket, Soccer, and Rugby.

You will be given a user question and a set of retrieved text chunks, each labeled with its source (sport, content type, page number).

Rules:
1. Answer ONLY using information present in the retrieved chunks. Do not use outside knowledge.
2. Some chunks may be bibliography/citation lists (URLs, "Retrieved from", author names, archive links) rather than substantive content -- ignore these when forming your answer, but you may still pull facts from chunks that mix substantive content with citation markers like [12].
3. If the chunks do not contain enough information to answer the question, say clearly: "I could not find this in the available sources." Do not guess or fill gaps with outside knowledge.
4. Do NOT include inline citations like "(sport, content_type, page N)" in your answer text -- sources are displayed separately to the user below the answer. Write in clean, natural prose without citation markers.
5. For cross-sport questions, address each sport explicitly before giving an overall conclusion, and note if one or more sports' sources didn't have relevant information.
6. Be concise -- a few sentences to a short paragraph, not an essay.
7. Some chunks contain compressed "infobox"-style data (short label-value pairs, e.g. "Holders South Africa (2023) Most titles New Zealand 3 Upcoming tournament 2027") rather than full sentences. Treat these labeled fields as facts and connect them to answer the question directly -- e.g. a "Holders" field with a year tells you who won the most recent tournament and when. This is using information present in the chunk, not outside knowledge.
8. Distinguish between citation NOISE (bare URLs, "Retrieved from...", "Archived from...", access dates, author names alone -- ignore these) and citation TITLES that state a fact (e.g. an article titled "ICC announces World Cup schedule: 14 teams in 2027 and 2031" -- the title itself is usable information, even though it appears in a numbered reference list). If a reference's title directly answers the question, use it and cite it normally.'''

# ---------------------------------------------------------------------------
# Router / retrieval / synthesis (same logic as the notebook)
# ---------------------------------------------------------------------------

def parse_router_response(raw):
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(cleaned.strip())


def route_query(question):
    response = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        temperature=0,
        system=ROUTER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    raw = response.content[0].text
    try:
        return parse_router_response(raw)
    except (json.JSONDecodeError, IndexError):
        return {"category": "cross_sport", "sports": ["cricket", "soccer", "rugby"], "sub_queries": {}}


def retrieve_for_query(question, top_k=3):
    route = route_query(question)
    category = route["category"]
    sports = route["sports"]
    sub_queries = route.get("sub_queries", {}) or {}

    if category == "out_of_scope":
        return route, []

    all_results = []
    for sport in sports:
        query_text = sub_queries.get(sport, question) if category == "cross_sport" else question
        filters = MetadataFilters(filters=[ExactMatchFilter(key="sport", value=sport)])
        retriever = index.as_retriever(similarity_top_k=top_k, filters=filters)
        results = retriever.retrieve(query_text)
        all_results.extend(results)

    return route, all_results


def format_chunks(results):
    if not results:
        return "No documents were retrieved."
    formatted = []
    for r in results:
        meta = r.metadata
        source = f"({meta.get('sport')}, {meta.get('content_type')}, page {meta.get('page_label')})"
        formatted.append(f"{source}:\n{r.text}")
    return "\n\n---\n\n".join(formatted)


def answer_query(question, top_k=3):
    route, results = retrieve_for_query(question, top_k=top_k)

    sources = [
        {
            "sport": r.metadata.get("sport"),
            "content_type": r.metadata.get("content_type"),
            "page": r.metadata.get("page_label"),
        }
        for r in results
    ]

    if route["category"] == "out_of_scope":
        return {
            "answer": "I can only answer questions about Cricket, Soccer, and Rugby (rules, history, and World Cup records). This question is outside that scope.",
            "route": route,
            "chunks_used": 0,
            "sources": [],
        }

    context = format_chunks(results)
    user_message = f"Question: {question}\n\nRetrieved context:\n\n{context}"

    response = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        temperature=0,
        system=SYNTHESIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return {
        "answer": response.content[0].text,
        "route": route,
        "chunks_used": len(results),
        "sources": sources,
    }

# ---------------------------------------------------------------------------
# Disk cache
# ---------------------------------------------------------------------------

def normalize_question(question):
    q = question.lower().strip()
    q = re.sub(r"[^\w\s]", "", q)
    q = re.sub(r"\s+", " ", q)
    return q


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def answer_query_cached(question, top_k=3):
    cache = load_cache()
    key = normalize_question(question)
    if key in cache:
        result = dict(cache[key])
        result["from_cache"] = True
        return result

    result = answer_query(question, top_k=top_k)
    result["from_cache"] = False
    cache[key] = {k: v for k, v in result.items() if k != "from_cache"}
    save_cache(cache)
    return result

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.title("🏏 ⚽ 🏉 Sports Knowledge Hub")
st.caption(
    "Explore rules, history, records, and World Cup statistics across Cricket, Soccer, and Rugby."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_route" not in st.session_state:
    st.session_state.last_route = None

with st.sidebar:
    st.header("About")
    st.markdown(
        "Covers **Cricket**, **Soccer**, and **Rugby** — rules, history, and "
        "World Cup records, drawn from 8 source documents."
    )

    st.divider()
    with st.expander("🔍 How this was answered", expanded=False):
        if st.session_state.last_route:
            info = st.session_state.last_route
            category_labels = {
                "rules": "📖 Rules lookup",
                "history": "📜 History / records lookup",
                "comparison": "⚖️ Comparison",
                "cross_sport": "🌍 Cross-sport search",
                "out_of_scope": "🚫 Outside scope",
            }
            st.markdown(f"**Type:** {category_labels.get(info['category'], info['category'])}")
            if info["sports"]:
                st.markdown(f"**Searched:** {', '.join(info['sports'])}")
            st.markdown(f"**Chunks used:** {info['chunks_used']}")
            cache_label = "✅ cache hit" if info["from_cache"] else "🔄 fresh"
            st.markdown(f"**Cache:** {cache_label}")
        else:
            st.caption("Ask a question to see routing info here.")

    st.divider()
    st.subheader("Frequently Asked Questions")
    demo_questions = [
        "How many times has Brazil won the World Cup?",
        "What are the rules for leg before wicket in cricket?",
        "Which country dominates the most sports at World Cup level?",
    ]
    for dq in demo_questions:
        if st.button(dq, use_container_width=True):
            st.session_state.pending_question = dq

    st.divider()
    if st.button("🗑️ Reset chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_route = None
        st.rerun()

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- {s['sport']} / {s['content_type']}, page {s['page']}")

# Handle input (typed or from a demo button)
question = st.chat_input("Ask about cricket, soccer, or rugby...")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = answer_query_cached(question)
        st.markdown(result["answer"])
        if result.get("sources"):
            with st.expander("Sources"):
                for s in result["sources"]:
                    st.markdown(f"- {s['sport']} / {s['content_type']}, page {s['page']}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result.get("sources", []),
    })

    st.session_state.last_route = {
        "category": result["route"]["category"],
        "sports": result["route"]["sports"],
        "chunks_used": result["chunks_used"],
        "from_cache": result["from_cache"],
    }