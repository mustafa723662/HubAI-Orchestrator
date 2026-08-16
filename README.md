# HubAI — AI Orchestrator

Unified AI router/orchestrator. Phase 2 uses Google Gemini Flash as the smart router.

## Phase 2 Scope

- `POST /api/v1/auth/register` — create an account (username + password), returns a JWT
- `POST /api/v1/auth/login` — log in, returns a JWT
- `POST /api/v1/route` — Gemini Flash analyzes the prompt and returns provider + refined prompt (decision only, no provider call)
- `POST /api/v1/execute` — 🔒 requires `Authorization: Bearer <token>`. Same routing decision, then actually calls the chosen provider, returns its output, and saves the run to the user's history
- `GET /api/v1/history` — 🔒 the logged-in user's last 5 runs, newest first
- `DELETE /api/v1/history` — 🔒 clears the logged-in user's history
- `GET /health` — health check
- Interactive API docs at `/docs`

### Auth

Accounts and prompt history are stored in a local SQLite database (`backend/hubai.db`, auto-created on first run, gitignored). Passwords are hashed with bcrypt; sessions are stateless JWTs (`JWT_SECRET_KEY` / `JWT_EXPIRE_MINUTES` in `.env`, default 7-day expiry). `/execute` and `/history` require a valid token — the frontend gates the whole app behind a login/register screen and attaches the token automatically.

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

> **Free-tier quota:** the default `GEMINI_MODEL` (`gemini-flash-lite-latest`) has its own daily free quota separate from other Gemini models. If routing starts returning `429 RESOURCE_EXHAUSTED`, that model's daily limit is exhausted — either wait for it to reset or point `GEMINI_MODEL` at a different available model (check `client.models.list()` for what your key currently has access to).

3. `JWT_SECRET_KEY` is already pre-filled with a random value in `backend/.env` — regenerate your own anytime with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

## Run

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Test

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Register + login:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/auth/register -Method POST -ContentType "application/json" -Body '{"username":"mustafa","password":"secret123"}'
```

This returns `{"access_token": "...", "token_type": "bearer", "user": {...}}`. Pass that token as `Authorization: Bearer <token>` on `/execute` and `/history` calls.

Smart route (requires `GEMINI_API_KEY`, no auth needed — decision only):

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

Execute (routes, then actually calls the provider, then saves the run to your history — requires the token from register/login):

```powershell
$token = (Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/auth/login -Method POST -ContentType "application/json" -Body '{"username":"mustafa","password":"secret123"}').access_token
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/execute -Method POST -ContentType "application/json" -Headers @{ Authorization = "Bearer $token" } -Body '{"prompt":"What is the capital of France?"}'
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
