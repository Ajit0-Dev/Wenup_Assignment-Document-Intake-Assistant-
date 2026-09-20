# Document Intake Assistant

A conversational LLM application that guides users through a structured personal wishes interview. It collects a defined set of fields via natural multi-turn conversation, maintains a validated **canonical state** (not just conversation history), and renders a real-time document preview.

> **Fictional document for demonstration purposes only — not legal advice.**

---

## Features

- **Multi-turn conversation** — natural follow-up questions, not a static form
- **Structured state management** — extracted fields validated before storage; conversation history is never the source of truth
- **Correction handling** — users can update previously confirmed fields at any time
- **Multiple-fact extraction** — captures several fields from a single message
- **Ambiguity detection** — asks for clarification instead of inventing values
- **Live information panel** — field-by-field progress view with confirmed/missing/unconfirmed status
- **Live document preview** — generated directly from the canonical state, updates on every turn
- **LLM provider abstraction** — supports Gemini (Google), OpenAI, and a deterministic mock for testing
- **Robust error handling** — malformed LLM output, API failures, and invalid inputs are all handled gracefully
- **39 automated backend tests + 3 frontend tests**

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    React / Vite Frontend               │
│  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   Chat Panel    │  │  Context Panel              │ │
│  │  (Conversation) │  │  Information Tab | Doc Tab  │ │
│  └────────┬────────┘  └──────────────┬──────────────┘ │
└───────────┼───────────────────────────┼────────────────┘
            │ REST API                  │ REST API
┌───────────▼───────────────────────────▼────────────────┐
│                   FastAPI Backend                      │
│                                                        │
│  POST /api/session  ──► Session Service                │
│  POST /api/chat     ──► Chat Route                     │
│                          │                             │
│                          ▼                             │
│                   LLM Service (abstract)               │
│                          │                             │
│            ┌─────────────┼─────────────┐              │
│            ▼             ▼             ▼              │
│         Mock LLM    Gemini LLM    OpenAI LLM          │
│                          │                             │
│                          ▼                             │
│              Pydantic Validation Layer                 │
│           (validate_and_apply_updates)                 │
│                          │                             │
│                          ▼                             │
│                  Canonical Intake State                │
│         (IntakeState — single source of truth)         │
│                          │                             │
│  GET /api/document/{id} ─┘                             │
│          Document Generator                            │
└────────────────────────────────────────────────────────┘
```

**Key design principle:** The LLM never directly mutates the application state. It proposes structured updates, which are fully validated by the application layer before being applied.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Data validation | Pydantic v2 |
| LLM Providers | Google Gemini (primary), OpenAI (optional) |
| Testing (backend) | pytest, pytest-asyncio, httpx |
| Testing (frontend) | Vitest, React Testing Library |
| Configuration | pydantic-settings, `.env` |

---

## Project Structure

```
Wneup/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── chat.py        # POST /api/chat
│   │   │       ├── document.py    # GET  /api/document/{session_id}
│   │   │       ├── health.py      # GET  /api/health
│   │   │       └── sessions.py    # POST /api/session
│   │   ├── core/
│   │   │   ├── config.py          # Settings (reads .env)
│   │   │   ├── prompts.py         # LLM system prompt
│   │   │   └── validation.py      # State validation & update logic
│   │   ├── models/
│   │   │   ├── intake_state.py    # IntakeState schema (source of truth)
│   │   │   ├── llm_contract.py    # LLMResponse / ProposedUpdate schemas
│   │   │   └── session.py         # Session model
│   │   ├── services/
│   │   │   ├── llm_service.py     # LLMService + Mock/Gemini/OpenAI impls
│   │   │   └── session_service.py # In-memory session store
│   │   └── main.py
│   ├── tests/
│   │   ├── test_chat.py           # Chat API tests
│   │   ├── test_document.py       # Document API tests
│   │   ├── test_e2e.py            # Full user journey test
│   │   ├── test_health.py         # Health check
│   │   ├── test_phase3.py         # LLM extraction & validation tests
│   │   ├── test_schemas.py        # Schema tests
│   │   └── test_sessions.py       # Session API tests
│   ├── .env.example
│   ├── .gitignore
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ChatPanel.tsx       # Conversation UI
    │   │   ├── ContextPanel.tsx    # Tab container
    │   │   ├── DocumentTab.tsx     # Live document preview
    │   │   └── InformationTab.tsx  # Structured state viewer
    │   ├── App.tsx                 # Root component & state
    │   ├── api.ts                  # API client
    │   └── index.css               # Global styles
    ├── vitest.setup.ts
    └── package.json
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Google Gemini API key (free tier works) — **or** set `LLM_PROVIDER=mock` to run without any API key

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY (or set LLM_PROVIDER=mock)
```

### 2. Frontend

```bash
cd frontend
npm install
```

---

## Run

### Backend

```bash
cd backend
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux

uvicorn app.main:app --reload --port 8000
```

Backend available at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

Frontend available at: http://localhost:5173

---

## Tests

### Backend (39 tests)

```bash
cd backend
venv\Scripts\activate
pytest -v
```

### Frontend (3 tests)

```bash
cd frontend
npm test
```

---

## Environment Variables

All configuration is read from `backend/.env`. Copy `backend/.env.example` and fill in your values.

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `mock`, `gemini`, or `openai` |
| `GEMINI_API_KEY` | If using Gemini | Your Google AI Studio API key |
| `GEMINI_MODEL` | No | Defaults to `gemini-3.5-flash-lite` |
| `OPENAI_API_KEY` | If using OpenAI | Your OpenAI API key |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o-mini` |

> **Never commit `.env` to version control.** It is listed in `.gitignore`.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/session` | Create a new conversation session |
| `POST` | `/api/chat` | Send a user message; returns assistant reply and updated state |
| `GET` | `/api/document/{session_id}` | Get the current document preview HTML |

### POST /api/chat — Request

```json
{
  "session_id": "uuid",
  "message": "My name is Alice and I live in London."
}
```

### POST /api/chat — Response

```json
{
  "session_id": "uuid",
  "assistant_message": "Thank you, Alice. Do you have any children?",
  "clarification_needed": null,
  "state": { ... }
}
```

---

## Design Decisions

### Structured state as source of truth
Conversation history is not parsed to produce the final document. Instead, each LLM response proposes structured field updates which are explicitly validated and applied. This means the document is always consistent with what was actually confirmed, regardless of conversational phrasing.

### LLM output is validated, never trusted directly
The LLM returns `ProposedUpdate` objects (field path, value, confidence, is_correction). The application validates each update independently against the `IntakeState` schema before accepting it. An invalid LLM suggestion cannot corrupt the state.

### LLM does not directly mutate state
The LLM is a black-box information extractor. It cannot write to the database or call any stateful APIs. It only produces a structured JSON response that is then evaluated by the application. This limits blast radius from hallucinations or prompt injection.

### Deterministic document generation
The document preview is generated by a pure function over the current `IntakeState`. It does not summarize conversation history. If a user corrects a field, the next document fetch reflects the corrected value immediately.

### Mock provider for testing
All automated tests run against `MockLLMService` — a deterministic rule-based extractor. This keeps the test suite fast, stable, and free of external dependencies.

---

## Limitations

- **In-memory sessions only**: Restarting the backend clears all sessions. A production system would use a persistent database.
- **Mock LLM is rule-based**: The `MockLLMService` matches simple trigger phrases. It does not cover all possible conversational inputs — it is for testing only.
- **No authentication**: Sessions are unauthenticated. Anyone with a session UUID can access it.
- **No rate limiting**: The backend does not limit API call frequency.
- **Single-server deployment**: The in-memory store is not distributed.

---

## Production Improvements

The following would be added in a real production system:

- **Persistent database** (PostgreSQL + SQLAlchemy) for durable session/state storage
- **Authentication & authorization** (JWT or OAuth2) to protect user data
- **Rate limiting** (per-user, per-session) to prevent abuse
- **LLM provider fallback** (e.g. Gemini → OpenAI) for resilience
- **Observability** (structured logging, tracing, Prometheus metrics)
- **Encrypted sensitive data** at rest
- **Stronger input validation and sanitization** including DOMPurify on the frontend
- **PDF export** of the final document
- **Audit trail** for all state changes
