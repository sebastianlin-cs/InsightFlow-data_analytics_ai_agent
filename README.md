# InsightFlow

InsightFlow is a data analysis agent platform.

## Current Stage

FastAPI backend with auth, dataset upload, data catalog, analysis sessions, and a minimal Agent API. React frontend foundation for the demo workflow.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- React
- Vite
- TypeScript
- Tailwind CSS
- LangGraph
- Pandas

## Frontend Dev

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

Backend URL:

```text
http://localhost:8000
```

## Optional LLM Planner/Response

v1.1 keeps the rule-based LangGraph/Pandas agent as the default. To enable an
OpenAI-compatible chat completions endpoint, set these backend `.env` values:

```text
LLM_ENABLED=false
LLM_PROVIDER=openai_compatible
LLM_API_KEY=
LLM_MODEL=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=30
```

When LLM config is disabled, missing, or invalid, `/api/agent/query` falls back
to the deterministic planner and template response generator.

