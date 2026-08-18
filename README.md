# HubAI — AI Orchestrator

Unified AI router/orchestrator. Phase 2 uses Google Gemini Flash as the smart router.

## Phase 2 Scope

- `POST /api/v1/auth/register` — create an account (username + password), returns a JWT
- `POST /api/v1/auth/login` — log in, returns a JWT
- `POST /api/v1/route` — Gemini Flash analyzes the prompt and returns provider + refined prompt (decision only, no provider call)
- `POST /api/v1/execute` — 🔒 requires `Authorization: Bearer <token>`. Same routing decision, then actually calls the chosen provider, returns its output, and saves the run to the user's history
- `GET /api/v1/history` — 🔒 the logged-in user's last 5 *conversations* (most recent turn each), newest first
- `GET /api/v1/history/{conversation_id}` — 🔒 the full turn-by-turn thread for one conversation, oldest first
- `DELETE /api/v1/history` — 🔒 clears the logged-in user's history
- `GET /api/v1/api-keys` — 🔒 status of the user's own BYOK keys (configured? masked preview, never the real value)
- `PUT /api/v1/api-keys/{provider}` — 🔒 save/replace the user's own key for `openai` or `claude`
- `DELETE /api/v1/api-keys/{provider}` — 🔒 remove the user's own key for that provider
- `GET /health` — health check
- Interactive API docs at `/docs`

### Auth

Accounts and prompt history are stored in a local SQLite database (`backend/hubai.db`, auto-created on first run, gitignored). Passwords are hashed with bcrypt; sessions are stateless JWTs (`JWT_SECRET_KEY` / `JWT_EXPIRE_MINUTES` in `.env`, default 7-day expiry). `/execute` and `/history` require a valid token — the frontend gates the whole app behind a login/register screen and attaches the token automatically.

> **Upgrading an existing local DB:** the conversation feature added a
> required `conversation_id` column to `prompt_history`. There's no
> migration tool wired up (just `Base.metadata.create_all()`, which only
> creates missing *tables*, not missing *columns*) — if your local
> `backend/hubai.db` predates this, delete it and let it recreate on next
> run. On Render's free plan this is a non-issue since the disk is already
> ephemeral (see below).

### Multi-turn conversations

`/execute` accepts an optional `conversation_id` in the request body. Omit it to start a new conversation (the response returns a freshly generated `conversation_id`); pass it back on the next call to continue that conversation — the backend reloads every prior turn from the DB, feeds it to the router (so Gemini can resolve references like "it"/"that" into a self-contained `refined_prompt`) and to the chosen provider (as real conversational context, for the text providers — image providers ignore it, since the refined prompt is already self-contained). The frontend's reply box under each response does this automatically; clicking a conversation in the history sidebar fetches its full thread via `GET /history/{conversation_id}` and lets you keep replying to it.

### BYOK — bring your own API key

Instead of relying on the system's `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`, each user can save their *own* key from the "API Anahtarlarım" (⚙️) panel in the header. Keys are encrypted at rest with [Fernet](https://cryptography.io/en/latest/fernet/) (`API_KEY_ENCRYPTION_KEY` in `.env`) — the plaintext key only ever exists in memory for the duration of the request that saves or uses it, never in the database. `GET /api-keys` only ever returns a masked preview (e.g. `sk-ab12...cd34`), never the real value.

At `/execute` time, priority is: **user's own key → system env key → Gemini fallback** (for text providers) **→ "not configured" note** (for `dalle`). DALL-E shares the user's `openai` key (same API).

### Provider status

| Provider | Status |
|---|---|
| `gemini` | ✅ Live — uses `GEMINI_API_KEY` |
| `openai` | ⏳ Wired up, needs `OPENAI_API_KEY` + `pip install openai` (see `requirements.txt`) |
| `dalle` | ⏳ Wired up, needs `OPENAI_API_KEY` + `pip install openai` (returns an image URL) |
| `claude` | ⏳ Wired up, needs `ANTHROPIC_API_KEY` + `pip install anthropic` |
| `midjourney` | ❌ No official public API — the router can still recommend it, but `/execute` can't call it |

When a provider isn't configured, `/execute` doesn't just dead-end:
- **`openai` / `claude`** (text providers): automatically falls back to Gemini so the user still gets a real answer. `status` is `"fallback"`, `provider` still shows the originally-routed provider (for transparency), and `detail` explains the substitution.
- **`dalle` / `midjourney`** (image providers): no fallback — Gemini's text reply isn't an image URL, so substituting it would render a broken image instead of a clean message. `status` is `"provider_not_configured"` / `"unsupported_provider"`, `output` is `null`, and `detail` explains what's missing.

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

3. `JWT_SECRET_KEY` and `API_KEY_ENCRYPTION_KEY` are already pre-filled with random values in `backend/.env` — regenerate your own anytime with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"                          # JWT_SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # API_KEY_ENCRYPTION_KEY
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

## Deployment (Render)

`render.yaml` at the repo root is a ready-to-use Blueprint for the backend.

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, point it at the repo. Render reads `render.yaml` and creates the web service (free plan, root dir `backend`).
3. Set the env vars Render prompts for (marked `sync: false` in `render.yaml`):
   - `GEMINI_API_KEY` — your key
   - `API_KEY_ENCRYPTION_KEY` — a Fernet key for encrypting users' BYOK keys, generated with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` (not the same one as your local `.env` — use a separate key per environment)
   - `ALLOWED_ORIGINS` — leave blank for now; come back and set it once the frontend is deployed (e.g. `https://your-frontend.netlify.app`)
   - `JWT_SECRET_KEY` is auto-generated by Render, no action needed.
4. Deploy the frontend as a static site (Netlify, Vercel, Cloudflare Pages, GitHub Pages — any of them work, it's one HTML file) from the `frontend/` folder.
5. In `frontend/index.html`, set `API_BASE` to your Render backend's URL (e.g. `https://hubai-backend.onrender.com`), redeploy the frontend.
6. Go back to Render and set `ALLOWED_ORIGINS` to the frontend's real deployed URL, so CORS allows it.

**Known limitations of this setup, worth knowing before relying on it:**
- **SQLite is ephemeral on Render's free plan** — the disk isn't persistent, so accounts/history reset on every redeploy or restart. For real persistence, either add a Render paid persistent disk, or point `DATABASE_URL` at a managed Postgres (Render/Neon/Supabase) — the code already supports this via `DATABASE_URL`, just uncomment `psycopg[binary]` in `requirements.txt`.
- **Gemini's free-tier daily quota (20 req/day, per model) is shared across every user of the deployed app.** `DAILY_GEMINI_CAP` (default 18) makes `/execute` fail fast with a clear message instead of a raw Gemini 429 once that's hit, but it doesn't create more quota — real usage will exhaust it fast. Move to a paid Gemini plan if you expect real traffic.
- The in-memory rate limiter (`slowapi`) and the daily cap counter are per-process — fine for Render's single free-tier instance, but won't work correctly if you ever scale to multiple workers/instances without moving that state to Redis.
