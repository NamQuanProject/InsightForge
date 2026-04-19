# InsightForge

InsightForge is a FastAPI backend for an agentic content workflow: it can analyze trends, generate personalized Vietnamese social content, manage generated assets, and support a human-approved posting flow.

The repository is intentionally backend. It connects with the InsightForce frontend ([Chris-KH/InsightForce](https://github.com/Chris-KH/InsightForce)). The frontend should talk to the API only; API usage details live in [app/api_docs.txt](app/api_docs.txt).

## What This Backend Provides

- A FastAPI API surface for users, trends, generated content, orchestration, and posting.
- A2A agents for trend analysis, content generation, orchestration, and posting.
- MCP tool servers for trend data, image generation, image retrieval, and social publishing helpers.
- PostgreSQL/Supabase persistence for users, trend analyses, generated content, image metadata, and publish-related data.
- A demo fast-path for UI testing so selected requests return fixed stored responses immediately without running the full agent workflow.

## Project Shape

```text
app/            FastAPI routes, schemas, services, database bootstrap
agents/         A2A agents for trend, content, routing, and posting
mcp_servers/    Tool servers used by the agents
database/       Supabase helper client
integrations_api/
                External integration wrappers
scripts/        Demo payloads and utility scripts
sample_data/    Local image metadata, embeddings, and image store data
sql/            Database bootstrap SQL
```

## Requirements

- Python 3.11+
- PostgreSQL-compatible database, usually Supabase
- API keys for the providers you want to run for real workflows
- Optional but recommended: a virtual environment

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file from `.env_example`, then replace values with your own credentials. Do not commit real secrets.

Minimum local settings usually include:

```env
DATABASE_URL=postgresql+asyncpg://...
AGENT_HOST=127.0.0.1
ROUTING_AGENT_PORT=9996
TREND_AGENT_PORT=9997
CONTENT_AGENT_PORT=9998
POSTING_AGENT_PORT=9995
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEMO_FAST_PATH_ENABLED=true
```

Add provider keys as needed for real agent runs:

```env
GOOGLE_API_KEY=...
SERP_API_KEY=...
ENSEMBLEDATA_API_KEY=...
UPLOAD_POST_API_KEY=...
IMG_BB_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

## Database

The FastAPI app calls `init_db()` on startup to create or update the application tables it knows about.

If you need to bootstrap manually, use:

```bash
psql "postgresql://USER:PASSWORD@HOST:PORT/DB?sslmode=require" -f sql/init_postgresql.sql
```

Use a normal PostgreSQL URL with `psql`, not the SQLAlchemy `postgresql+asyncpg://` form.

## Running The API

Start the FastAPI backend:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET http://127.0.0.1:8000/health
```

## Running The Full Agent Workflow

The full orchestration path expects the agent servers to be running:

```bash
python -m agents.trend_agent.main
python -m agents.generating_agent.main
python -m agents.posting_agent.main
python main.py
```

Then call:

```text
POST /api/v1/agents/orchestrate
```

The routing server in `main.py` coordinates the trend and content agents. Full runs can take a while because they may call LLMs, trend providers, image generation, image storage, and database persistence.


## Main API Areas

Use [app/api_docs.txt](app/api_docs.txt) for request and response fields. The practical UI entry points are:

- `GET /health`
- `GET /api/v1/agents/status`
- `POST /api/v1/agents/orchestrate`
- `POST /api/v1/post/post`
- `GET /api/v1/contents`
- `GET /api/v1/contents/{content_id}`
- `GET /api/v1/trends/history`
- `POST /api/v1/trends/history/search`
- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`



## Development Notes

- Keep edits scoped to the backend repository.
- Restart FastAPI after service or schema changes.
- Restart agent servers after agent prompt/tool changes.
- If the UI seems slow, confirm whether the request matches the demo fast-path sample exactly.
- If image retrieval fails on Windows, check that JSON metadata is read with UTF-8.
- Keep `.env`, credentials, and provider keys out of git.

## Troubleshooting

Agents unreachable:

```text
GET /api/v1/agents/status
```

Slow orchestration:

- Confirm `DEMO_FAST_PATH_ENABLED=true` for demo mode.
- Confirm the prompt matches `scripts/script_orchestrator.json`.
- If running the real workflow, check all agent processes and provider credentials.

Posting flow returns slowly:

- Confirm the request matches one item in `scripts/script_upload.json`.
- If using the real posting workflow, make sure the posting agent and its MCP server can access image metadata and provider credentials.

Database errors:

- Check `DATABASE_URL`.
- Confirm Supabase/PostgreSQL allows SSL if required.
- Restart the backend so `init_db()` can run.

