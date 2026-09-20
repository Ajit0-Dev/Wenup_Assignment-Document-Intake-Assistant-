# Document Intake Assistant — Backend

FastAPI backend for the Document Intake Assistant.

> See the [root README](../README.md) for full project documentation, setup, and architecture.

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate   # Windows | source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env    # then edit .env with your API key
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/session` | Create conversation session |
| `POST` | `/api/chat` | Send message; receive reply + updated state |
| `GET` | `/api/document/{session_id}` | Get document preview HTML |

## Environment Variables

See `.env.example` for required configuration. Key variables:

- `LLM_PROVIDER` — `mock` (testing, no API key) | `gemini` | `openai`
- `GEMINI_API_KEY` — required if using Gemini
- `GEMINI_MODEL` — defaults to `gemini-3.5-flash-lite`

