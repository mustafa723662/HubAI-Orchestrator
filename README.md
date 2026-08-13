# HubAI — AI Orchestrator

Unified AI router/orchestrator. Phase 2 uses Google Gemini Flash as the smart router.

## Phase 2 Scope

- `POST /api/v1/route` — Gemini Flash analyzes the prompt and returns provider + refined prompt (decision only, no provider call)
- `POST /api/v1/execute` — same routing decision, then actually calls the chosen provider and returns its output
- `GET /health` — health check
- Interactive API docs at `/docs`

### Provider status

| Provider | Status |
|---|---|
| `gemini` | ✅ Live — uses `GEMINI_API_KEY` |
| `openai` | ⏳ Wired up, needs `OPENAI_API_KEY` + `pip install openai` (see `requirements.txt`) |
| `dalle` | ⏳ Wired up, needs `OPENAI_API_KEY` + `pip install openai` (returns an image URL) |
| `claude` | ⏳ Wired up, needs `ANTHROPIC_API_KEY` + `pip install anthropic` |
| `midjourney` | ❌ No official public API — the router can still recommend it, but `/execute` can't call it |

When a provider isn't configured, `/execute` returns `status: "provider_not_configured"` (or `"unsupported_provider"` for Midjourney) instead of failing the whole request — `output` is `null` and `detail` explains what's missing.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### API Key (required for routing)

1. Copy the env template:

```powershell
copy .env.example .env
```

2. Open `backend/.env` and paste your Gemini API key:

```env
GEMINI_API_KEY=your_actual_key_here
```

Get a key at: https://aistudio.google.com/apikey

## Run

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Test

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Smart route (requires `GEMINI_API_KEY`):

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/route -Method POST -ContentType "application/json" -Body '{"prompt":"Draw a cyberpunk city at night"}'
```

Example response:

```json
{
  "provider": "midjourney",
  "refined_prompt": "...",
  "reasoning": "...",
  "original_prompt": "Draw a cyberpunk city at night"
}
```

Execute (routes, then actually calls the provider):

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/execute -Method POST -ContentType "application/json" -Body '{"prompt":"What is the capital of France?"}'
```

Example response:

```json
{
  "provider": "gemini",
  "refined_prompt": "...",
  "reasoning": "...",
  "original_prompt": "What is the capital of France?",
  "status": "ok",
  "output": "Paris.",
  "detail": null
}
```

Swagger UI: http://127.0.0.1:8000/docs
