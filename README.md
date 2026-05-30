# Capstone Conversational RAG Assistant

A production-ready **multi-agent AI customer support pipeline** built with LangGraph, Groq LLaMA 3.3 70B, FAISS RAG, and FastAPI. Customers interact through a professional chat UI that streams live agent-processing steps in real time.

---

## Architecture

```
User Message (POST /complaint/stream)
          │
          ▼
┌─────────────────────────┐
│  Agent 1 — Classifier   │  Groq LLaMA 3.3 70B
│  Intent + Confidence    │  5 intents · confidence score 0–1
└────────────┬────────────┘
             │
     ┌───────▼────────┐
     │ LangGraph Router│
     └───┬────────┬───┘
         │        │
   escalate     normal
         │        │
         ▼        ▼
  ┌──────────┐  ┌─────────────────────────┐
  │Escalation│  │  Agent 2 — Policy Lookup │  FAISS + HuggingFace
  │  Node    │  │  RAG · intent namespaces │  Embeddings
  └──────────┘  └───────────┬─────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Agent 3 — Drafter    │  Groq LLaMA 3.3 70B
                │  Tone-aware response  │  Multi-turn history
                └───────────┬───────────┘
                            │
                            ▼
                   Final Response (SSE)
```

---

## Features

- **Multi-agent pipeline** — Intent classification → Policy retrieval → Response drafting
- **LangGraph orchestration** — Conditional escalation routing, shared state across agents
- **RAG with FAISS** — Per-intent vector namespaces (complaint, refund, product_info, escalate, general)
- **Groq LLaMA 3.3 70B** — Fast LLM inference for both classification and drafting
- **HuggingFace embeddings** — Local `all-MiniLM-L6-v2`, no OpenAI key needed
- **Multi-turn conversations** — Full history passed to the drafter for contextual replies
- **SSE streaming** — Live per-node agent steps displayed in the UI
- **Professional chat UI** — Online 24/7 status, pipeline diagram modal, suggestion chips
- **65 tests** — Unit tests for classifier, retriever, and full E2E pipeline

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq · LLaMA 3.3 70B Versatile |
| Orchestration | LangGraph |
| Vector Store | FAISS (per-intent namespaces) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Backend | FastAPI + Uvicorn |
| Frontend | Vanilla HTML / CSS / JS (SSE streaming) |
| PDF Ingestion | LangChain PyPDFLoader |
| Testing | Pytest |

---

## Project Structure

```
capstone_rag/
├── agent1/
│   └── classifier.py        # Intent classifier (Groq)
├── agent2/
│   ├── vector_store.py      # FAISS index management
│   ├── retriever.py         # Top-k policy chunk retrieval
│   └── routing.py           # Intent → namespace routing map
├── agent3/
│   ├── drafter.py           # Response drafter (Groq)
│   └── prompts.py           # Tone-aware system prompt templates
├── shared/
│   └── state.py             # AgentState dataclass + GraphState TypedDict
├── orchestrator.py          # LangGraph pipeline graph
├── app.py                   # FastAPI app (REST + SSE endpoints)
├── frontend/
│   └── index.html           # Single-file chat UI
├── scripts/
│   ├── ingest_docs.py       # CLI: ingest PDFs into FAISS
│   └── create_sample_policies.py  # Generate sample policy PDFs
├── tests/
│   ├── test_classifier.py   # 22 classifier unit tests
│   ├── test_retriever.py    # 29 retriever unit tests
│   └── test_e2e.py          # 14 end-to-end pipeline tests
├── data/
│   └── policies/            # Source PDF policy documents
├── .env.example             # Environment variable template
└── requirements.txt
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/SumitSrivastava87/Capstone_Conversational_RAG_Assistant.git
cd Capstone_Conversational_RAG_Assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=gsk_your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

### 4. Ingest policy documents

Run the sample policy generator and ingest into FAISS:

```bash
python scripts/create_sample_policies.py

python scripts/ingest_docs.py --file data/policies/complaint/complaint_policy.pdf --intent complaint
python scripts/ingest_docs.py --file data/policies/refund/refund_policy.pdf --intent refund
python scripts/ingest_docs.py --file data/policies/product_info/product_info_policy.pdf --intent product_info
python scripts/ingest_docs.py --file data/policies/escalate/escalation_policy.pdf --intent escalate
python scripts/ingest_docs.py --file data/policies/general/general_policy.pdf --intent general
```

To add your own policy documents:

```bash
python scripts/ingest_docs.py --file your_policy.pdf --intent refund
```

### 5. Start the server

```bash
uvicorn app:app --reload
```

Open **http://localhost:8000** in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the chat UI |
| `POST` | `/complaint` | Full pipeline, returns JSON result |
| `POST` | `/complaint/stream` | SSE stream of per-agent steps |

### Request body

```json
{
  "message": "I'd like a refund for my order",
  "history": [
    { "role": "user", "content": "My item arrived damaged" },
    { "role": "assistant", "content": "We are sorry to hear that..." }
  ]
}
```

### Response (SSE events)

```
data: {"node": "classify", "data": {"intent": "refund", "confidence": 0.97}}
data: {"node": "retrieve", "data": {"policy_chunks": [...], "source_refs": [...]}}
data: {"node": "draft",    "data": {"draft_response": "..."}}
data: {"node": "done",     "data": { ...full final state... }}
```

---

## Intent Classes

| Intent | Description |
|---|---|
| `complaint` | Customer unhappy with a product or service |
| `refund` | Return, refund, or exchange request |
| `product_info` | Product details, warranty, specifications |
| `escalate` | Requests manager or expresses extreme frustration |
| `general` | Any other enquiry |

> Queries with confidence below **70%** are automatically escalated.

---

## Running Tests

```bash
pytest tests/ -v
```

All 65 tests run without an API key (LLM calls are mocked).

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | **Required.** Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `FAISS_INDEX_DIR` | `data/indexes` | Path to FAISS index storage |
| `CLASSIFIER_CONFIDENCE_THRESHOLD` | `0.70` | Below this → auto-escalate |
