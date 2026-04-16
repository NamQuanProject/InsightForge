# InsightForge

InsightForge is an agentic content intelligence and publishing system for creators. It combines trend research, content generation, image generation, social posting, account synchronization, and persistent history behind a FastAPI backend.

The current codebase is not only a concept document. It contains a working backend, multiple A2A agents, MCP tool servers, Upload-Post integration, Supabase/PostgreSQL persistence, mock platform analytics for UI wiring, and image retrieval support for the posting workflow.

## What The System Does

InsightForge helps a creator move from a content idea to a published social post:

1. Analyze trend signals from Google Trends and TikTok.
2. Generate Vietnamese content assets from the trend report.
3. Produce video scripts, captions, platform posts, music direction, and image prompts.
4. Generate section images through Cloudflare Workers AI.
5. Publish text, photo, or video posts through Upload-Post.
6. Sync the creator's Upload-Post account, profiles, connected social accounts, and publish history into Supabase/PostgreSQL.
7. Expose everything through FastAPI endpoints for a frontend or external client.

## High-Level Architecture

```text
Client / Frontend
    |
    v
FastAPI backend (app/main.py)
    |
    |-- Users, trends, content, post, Upload-Post, platform endpoints
    |-- SQLAlchemy async persistence to PostgreSQL / Supabase
    |-- Supabase client for image store and posting-agent thread metadata
    |
    v
A2A agent network
    |
    |-- RoutingAgent          : orchestrates trend + content agents
    |-- TrendingAnalysisAgent : Google Trends + TikTok intelligence
    |-- ContentGeneratingAgent: scripts, captions, images, music direction
    |-- PostingAgent          : human-in-the-loop social publishing
    |
    v
MCP tool servers
    |
    |-- trends_servers        : SerpAPI / Google Trends tools
    |-- social_media_servers  : EnsembleData / TikTok tools
    |-- generating_servers    : Cloudflare image generation
    |-- posting_servers       : Upload-Post publishing + image RAG
```

## Core Workflows

### 1. Trend Analysis

Entry points:

- `POST /api/v1/trends/analyze`
- `POST /api/v1/agents/orchestrate`
- `agents/trend_agent/main.py`

Flow:

```text
User query
  -> TrendService
  -> TrendAgent
  -> MCP google_trends + social_media_trends tools
  -> structured trend report
  -> trend_analyses table
```

The trend agent uses:

- SerpAPI Google Trends data.
- EnsembleData TikTok search data.
- Deterministic scoring helpers for velocity, engagement, and momentum.
- JSON repair fallback when model output is malformed.

### 2. Content Generation

Entry points:

- `POST /api/v1/contents/generate`
- `POST /api/v1/agents/orchestrate`
- `agents/generating_agent/main.py`

Flow:

```text
Prompt or saved trend analysis
  -> ContentService
  -> ContentGenerationAgent
  -> image_generation MCP tool
  -> generated content bundle
  -> generated_contents table
```

Generated content contains:

- `selected_keyword`
- `main_title`
- `video_script`
- per-section thumbnail prompts
- platform posts for TikTok, Facebook, and Instagram
- `music_background`

The content agent is instructed to write user-facing content in Vietnamese and image prompts in English.

### 3. Full Orchestration

Entry point:

- `POST /api/v1/agents/orchestrate`

Flow:

```text
Prompt
  -> RoutingAgent on ROUTING_AGENT_PORT
  -> call_trend_agent tool
  -> call_content_agent tool
  -> normalized output
  -> trend_analyses + generated_contents tables
  -> optional JSON files on disk
```

The backend client for this is `app/services/a2a_client.py`. It sends JSON-RPC `message/send` payloads to the routing A2A server and normalizes the final JSON into the backend schema.

### 4. Upload-Post Account Sync And Publishing

Entry points:

- `GET /api/v1/upload-post/account/me`
- `GET /api/v1/upload-post/users`
- `POST /api/v1/upload-post/publish`
- `GET /api/v1/upload-post/history`
- `GET /api/v1/upload-post/publish-jobs`
- `scripts/sync_upload_post_user.py`

Flow:

```text
Upload-Post API key
  -> /uploadposts/me
  -> /uploadposts/users
  -> app user upsert
  -> users table stores account, profiles, social accounts, connected platforms
```

Publishing supports:

- text posts
- photo posts
- video posts
- scheduling
- first comments
- tags
- public asset URLs
- uploaded files
- multiple Upload-Post platforms

Supported platform names in the backend publisher:

```text
tiktok, instagram, youtube, facebook, x, threads, linkedin,
bluesky, reddit, pinterest, google_business
```

### 5. Posting Agent With Human Approval

Entry points:

- `POST /api/v1/post/post`
- `POST /api/v1/post/upload_image`
- `agents/posting_agent/main.py`

The posting agent uses a human-in-the-loop LangChain middleware. Upload tools require approval before execution. The posting MCP server can:

- upload text, photos, and videos through Upload-Post
- read Upload-Post history, media, analytics, and profiles
- retrieve uploaded images through local embedding search
- convert local images to public URLs through ImgBB

### 6. Platform Dashboard Data

Entry points:

- `/api/v1/youtube/*`
- `/api/v1/tiktok/*`

These endpoints serve structured mock analytics from CSV files under:

- `app/mock_data/youtube`
- `app/mock_data/tiktok`

They are useful for frontend dashboards while real platform analytics are being integrated.

## FastAPI Endpoints

### Health

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Backend health check. |

### Users

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/v1/users` | Create an app user. |
| GET | `/api/v1/users` | List users with Upload-Post account data, profiles, connected platforms, and history counts. |
| GET | `/api/v1/users/{user_id}` | Get one full user record. |

User records include:

- email
- name
- plan
- Upload-Post account payload
- Upload-Post profiles
- social accounts by platform
- connected platforms
- trend/content/publish counts

### Agents

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/agents/status` | Check whether routing, trend, and content agent ports are reachable. |
| POST | `/api/v1/agents/orchestrate` | Run the full agent pipeline and persist results. |

### Trends

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/v1/trends/analyze` | Run the trend agent and persist a trend analysis. |
| GET | `/api/v1/trends/history` | List saved trend analyses. |
| GET | `/api/v1/trends/{analysis_id}` | Get one saved trend analysis. |
| GET | `/api/v1/trends/mock/overview` | Lightweight mock overview for UI wiring. |

### Content

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/v1/contents/generate` | Generate content from a prompt or saved trend analysis. |
| GET | `/api/v1/contents` | List generated content records. |
| GET | `/api/v1/contents/{content_id}` | Get one generated content record. |

### Upload-Post

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/upload-post/account/me` | Fetch real Upload-Post account and profiles, then upsert the app user. |
| POST | `/api/v1/upload-post/users` | Create an Upload-Post profile. |
| GET | `/api/v1/upload-post/users` | List Upload-Post profiles. |
| GET | `/api/v1/upload-post/users/{username}` | Get one Upload-Post profile. |
| DELETE | `/api/v1/upload-post/users/{username}` | Delete an Upload-Post profile. |
| POST | `/api/v1/upload-post/jwt/generate` | Generate an Upload-Post connection JWT/access URL. |
| POST | `/api/v1/upload-post/jwt/validate` | Validate an Upload-Post JWT. |
| POST | `/api/v1/upload-post/publish` | Publish text, photo, or video content through Upload-Post. |
| GET | `/api/v1/upload-post/publish-jobs` | List saved publish jobs. |
| GET | `/api/v1/upload-post/publish-jobs/{publish_job_id}` | Get one saved publish job. |
| GET | `/api/v1/upload-post/history` | Fetch Upload-Post upload history. |
| GET | `/api/v1/upload-post/analytics/profiles/{profile_username}` | Fetch profile analytics. |
| GET | `/api/v1/upload-post/analytics/profiles/{profile_username}/total-impressions` | Fetch impression totals. |
| GET | `/api/v1/upload-post/analytics/posts/{request_id}` | Fetch post analytics. |
| GET | `/api/v1/upload-post/interactions/comments` | Fetch post comments. |

### YouTube And TikTok Dashboard APIs

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/youtube/channel/status` | Mock YouTube channel status. |
| GET | `/api/v1/youtube/trends` | Mock YouTube trend dashboard data. |
| GET | `/api/v1/youtube/recommendations` | Mock YouTube recommendations. |
| GET | `/api/v1/youtube/videos` | Mock YouTube video list. |
| GET | `/api/v1/youtube/videos/{video_id}` | One mock YouTube video. |
| POST | `/api/v1/youtube/upload` | Upload a YouTube video through the `upload-post` package. |
| GET | `/api/v1/tiktok/channel/status` | Mock TikTok channel status. |
| GET | `/api/v1/tiktok/trends` | Mock TikTok trend dashboard data. |
| GET | `/api/v1/tiktok/recommendations` | Mock TikTok recommendations. |
| GET | `/api/v1/tiktok/videos` | Mock TikTok video list. |
| GET | `/api/v1/tiktok/videos/{video_id}` | One mock TikTok video. |
| POST | `/api/v1/tiktok/upload` | Upload a TikTok video through the `upload-post` package. |

### Posting

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/v1/post/post` | Send a posting request to the PostingAgent. |
| POST | `/api/v1/post/upload_image` | Store an image, embed it, upload it to ImgBB, and save metadata. |

## Data Model

The SQLAlchemy models live in `app/models.py`; the bootstrap SQL lives in `sql/init_postgresql.sql`.

### `users`

Stores app users plus synced Upload-Post identity data:

- `email`
- `name`
- `plan`
- `upload_post_account`
- `profiles`
- `social_accounts`
- `connected_platforms`

### `trend_analyses`

Stores trend reports from the trend agent or orchestration flow:

- original query
- structured trend results
- markdown summary
- status and error metadata

### `generated_contents`

Stores content bundles from the content agent:

- selected keyword
- main title
- video script
- platform posts
- music background
- full raw output

### `publish_jobs`

Stores local records of Upload-Post publish requests:

- profile username
- platforms
- title, description, tags
- post kind
- provider request/job IDs
- full provider response
- status

## Repository Layout

```text
app/
  api/                  FastAPI route modules
  schema/               Pydantic request/response models
  services/             Backend service layer
  mock_data/            CSV dashboard data for YouTube and TikTok
agents/
  trend_agent/          TrendAnalysis A2A agent
  generating_agent/     ContentGeneration A2A agent
  orchestration_agent/  Routing A2A agent and sub-agent tools
  posting_agent/        Human-in-the-loop posting agent
mcp_servers/
  trends_servers/       Google Trends / SerpAPI tools
  social_media_servers/ TikTok / EnsembleData tools
  generating_servers/   Cloudflare image generation tools
  posting_servers/      Upload-Post + image retrieval tools
integrations_api/       External API wrappers
database/               Supabase helper client and lightweight models
sql/                    PostgreSQL bootstrap SQL
scripts/                Utility scripts, including Upload-Post user sync
sample_outputs/         Example generated payloads
images/                 Generated image output directory
```

## Environment Variables

Create a local `.env` file. Do not commit real secrets.

Core backend:

```env
DATABASE_URL=postgresql+asyncpg://...
HOST=localhost
AGENT_HOST=localhost
ROUTING_AGENT_PORT=9996
TREND_AGENT_PORT=9997
CONTENT_AGENT_PORT=9998
POSTING_AGENT_PORT=9995
ORCHESTRATOR_TIMEOUT=420
ORCHESTRATOR_OUTPUT_DIR=.
```

LLM and agent keys:

```env
GOOGLE_API_KEY=...
GEMINI_API_KEY=...
OPENAI_API_KEY=...
TREND_AGENT_MODEL=gemini/gemini-2.5-flash
CONTENT_AGENT_MODEL=gemini/gemini-2.5-flash
ROUTING_AGENT_MODEL=gemini:gemini-2.5-flash
```

Trend and social data:

```env
SERP_API_KEY=...
ENSEMBLEDATA_API_KEY=...
```

Upload-Post:

```env
UPLOAD_POST_API_KEY=...
UPLOAD_POST_BASE_URL=https://api.upload-post.com/api
UPLOAD_POST_TIMEOUT_SECONDS=120
UPLOAD_POST_DEFAULT_USER=...
UPLOAD_POST_YOUTUBE_USER=...
UPLOAD_POST_TIKTOK_USER=...
UPLOAD_POST_INSTAGRAM_USER=...
```

Image generation and image publishing:

```env
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
IMG_BB_API_KEY=...
```

Supabase helper client:

```env
SUPABASE_URL=...
SUPABASE_KEY=...
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize the database with SQL if needed. If you use `psql`, pass a normal PostgreSQL URL, not the SQLAlchemy `postgresql+asyncpg://` form:

```bash
psql "postgresql://USER:PASSWORD@HOST:PORT/DB?sslmode=require" -f sql/init_postgresql.sql
```

The FastAPI app also calls `init_db()` on startup. It creates missing SQLAlchemy tables and adds the Upload-Post JSON columns to existing `users` tables.

## Running The System

Start all A2A agents and the routing server:

```bash
python -m agents.posting_agent.main
python -m agents.trend_agent.main
python -m agents.generating_agent.main
python main.py
```

The helper script `run.sh` contains the same sequence:

```bash
sh run.sh
```

Start the FastAPI backend:

```bash
uvicorn app.main:app --reload
```

Backend docs:

```text
http://localhost:8000/docs
```

Sync the real Upload-Post user into Supabase/PostgreSQL:

```bash
python scripts/sync_upload_post_user.py
```

## Example API Calls

Analyze a trend:

```bash
curl -X POST http://localhost:8000/api/v1/trends/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"AI video automation in Vietnam","limit":3}'
```

Run the full orchestrator:

```bash
curl -X POST http://localhost:8000/api/v1/agents/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Analyze trends and generate TikTok content about AI video tools","save_files":true}'
```

Sync Upload-Post account and profiles:

```bash
curl http://localhost:8000/api/v1/upload-post/account/me
```

Publish a text post through Upload-Post:

```bash
curl -X POST http://localhost:8000/api/v1/upload-post/publish \
  -F "platforms=youtube" \
  -F "title=InsightForge demo post" \
  -F "description=Published through Upload-Post"
```

The `user` form field is optional when `UPLOAD_POST_<PLATFORM>_USER` or `UPLOAD_POST_DEFAULT_USER` is configured.

## Current Implementation Notes

- The YouTube and TikTok dashboard APIs use local CSV mock data.
- Upload-Post account, profile, history, analytics, comments, and publishing routes call the real Upload-Post API when credentials are configured.
- The posting agent has a human approval workflow before upload tools execute.
- Image RAG stores local embeddings under `sample_data/embeddings` and metadata under `sample_data/metadata.json`.
- Generated section images are saved under `images/`.
- Several test and sample files under `agent_test/`, `sample_outputs/`, and root JSON outputs are developer artifacts for integration checks.

## Security Notes

- Keep `.env` out of git.
- Do not commit live API keys or service account credentials.
- Rotate any key that has ever been committed or shared.
- Use separate development and production Upload-Post/Supabase projects when possible.

## Vision

InsightForge is a creator operations backend: it watches trend signals, turns them into actionable content, supports human-reviewed publishing, and keeps the creator's cross-platform account state in one place.
