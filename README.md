# AI GitHub Code Reviewer

A production-oriented web application for analyzing GitHub repositories and pull requests using a local LLM via [Ollama](https://ollama.com). Everything runs locally with no paid API dependencies.

## Overview

AI GitHub Code Reviewer helps developers inspect code quality across multiple languages, surface issues with severity and confidence scores, and generate structured review reports. The application stores review history in PostgreSQL and provides a modern dashboard for browsing results.

**Current status:** Foundation, JWT authentication, GitHub cloning, static analysis, Ollama AI reviews, report export, review search, and per-user settings are implemented.

## Screenshots

| Dashboard | Review History |
|-----------|----------------|
| ![Dashboard](docs/images/dashboard.png) | ![Review History](docs/images/history.png) |

## Architecture

```mermaid
flowchart TB
  subgraph frontend [Frontend]
    Pages[React Pages]
    RQ[React Query]
    Client[API Client]
  end

  subgraph backend [Backend FastAPI]
    API[api layer]
    Services[services layer]
    Repos[repositories layer]
    Models[SQLAlchemy models]
  end

  subgraph infra [Infrastructure]
    PG[(PostgreSQL)]
    Ollama[Ollama]
  end

  Pages --> RQ --> Client
  Client -->|REST JSON| API
  API --> Services
  Services --> Repos
  Repos --> Models
  Models --> PG
  Services -.-> Ollama
```

### Layer responsibilities

| Layer | Responsibility |
|-------|----------------|
| `api/` | HTTP routes, request validation, dependency injection |
| `services/` | Business logic, orchestration |
| `repositories/` | Database queries |
| `models/` | SQLAlchemy ORM definitions |
| `schemas/` | Pydantic request/response DTOs |
| `workers/` | Background jobs (future) |

**Dependency rule:** Routes call services only. Services call repositories and external clients. Repositories interact with the database exclusively.

## Tech Stack

| Area | Technologies |
|------|-------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Query, React Router |
| AI | Ollama (Qwen2.5 default) |
| Auth | JWT, bcrypt (planned) |
| Infrastructure | Docker, Docker Compose |
| Quality | Ruff, Black, mypy, pytest, ESLint, Prettier, pre-commit |
| CI | GitHub Actions |

## Quick Start (Docker)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Ollama](https://ollama.com) installed locally (optional for Step 1; required for AI reviews)

### Run

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

To include the Ollama container:

```bash
docker compose --profile ai up --build
```

When using the Docker Ollama service, set `OLLAMA_BASE_URL=http://ollama:11434` in `.env` and pull a model:

```bash
docker compose exec ollama ollama pull qwen2.5
```

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install ".[dev]"

# Start PostgreSQL (via Docker or local install)
export DATABASE_URL=postgresql+psycopg://reviewer:reviewer@localhost:5432/reviewer

uvicorn app.main:app --reload --port 8000
pytest
ruff check .
mypy app
```

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run test
npm run lint
```

### Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### GitHub Actions CI

The CI workflow template lives at [`docs/ci-workflow.example.yml`](docs/ci-workflow.example.yml).

GitHub blocks pushes of workflow files when your HTTPS token lacks the **workflow** scope. To enable CI:

1. **GitHub web UI (easiest):** In your repo, create `.github/workflows/ci.yml` and paste the contents of `docs/ci-workflow.example.yml`.
2. **Personal Access Token:** Create a [classic PAT](https://github.com/settings/tokens) with **repo** and **workflow** scopes, then push after copying the example file to `.github/workflows/ci.yml`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `reviewer` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `reviewer` | PostgreSQL password |
| `POSTGRES_DB` | `reviewer` | PostgreSQL database name |
| `DATABASE_URL` | — | SQLAlchemy connection string |
| `JWT_SECRET` | — | Secret for signing JWT tokens |
| `DEBUG` | `false` | Enable debug mode |
| `APP_NAME` | `AI GitHub Code Reviewer` | Application title |
| `API_V1_PREFIX` | `/api/v1` | API route prefix |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (comma-separated) |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5` | Default LLM model |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Ollama request timeout |
| `AI_MAX_FILES` | `10` | Max files sent to the LLM per review |
| `AI_MAX_CHARS_PER_FILE` | `4000` | Max characters per file in AI prompts |
| `AI_TEMPERATURE` | `0.2` | LLM sampling temperature |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API base URL |
| `GITHUB_CLIENT_ID` | — | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | — | GitHub OAuth App client secret |
| `GITHUB_OAUTH_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/github/callback` | OAuth callback URL registered with GitHub |
| `GITHUB_OAUTH_SCOPES` | `read:user user:email` | GitHub OAuth scopes |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend base URL for post-login redirects |
| `REPOS_WORKSPACE_ROOT` | `./.repos` | Local path for cloned repositories |
| `GIT_CLONE_DEPTH` | `1` | Shallow clone depth |
| `GIT_CLONE_TIMEOUT_SECONDS` | `300` | Git clone timeout |

Copy `.env.example` to `.env` and adjust values for your environment.

### GitHub OAuth setup

1. Create a [GitHub OAuth App](https://github.com/settings/developers) (OAuth Apps, not GitHub Apps).
2. Set **Authorization callback URL** to `http://localhost:8000/api/v1/auth/github/callback` (or your deployed backend callback URL).
3. Copy the **Client ID** and generate a **Client secret** into `.env` as `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`.
4. Ensure `FRONTEND_URL` matches where the React app is served (default `http://localhost:5173`).
5. Restart the backend after updating environment variables.

Sign-in flow: the frontend redirects to `/api/v1/auth/github/login`, GitHub returns to the backend callback, and the backend redirects to the frontend with a short-lived exchange code that is swapped for JWT tokens via `POST /api/v1/auth/github/exchange`.

## API Documentation

Interactive Swagger UI is available at `/docs` when the backend is running.

### Health endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Liveness check |
| `GET` | `/api/v1/ready` | Readiness check (includes database) |
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Sign in |
| `GET` | `/api/v1/auth/github/login` | Start GitHub OAuth (redirect) |
| `GET` | `/api/v1/auth/github/callback` | GitHub OAuth callback (redirect) |
| `POST` | `/api/v1/auth/github/exchange` | Exchange OAuth code for JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/auth/me` | Current user (Bearer token required) |
| `GET` | `/api/v1/repositories` | List cloned repositories |
| `POST` | `/api/v1/repositories` | Clone a GitHub repository |
| `GET` | `/api/v1/repositories/{id}` | Repository details |
| `DELETE` | `/api/v1/repositories/{id}` | Delete repository and workspace files |
| `POST` | `/api/v1/repositories/{id}/analyze` | Run static analysis |
| `POST` | `/api/v1/repositories/{id}/ai-review` | Run Ollama AI review |
| `GET` | `/api/v1/repositories/{id}/reviews` | List analysis runs |
| `GET` | `/api/v1/repositories/{id}/reviews/latest` | Latest run (`?review_type=static\|ai`) |
| `GET` | `/api/v1/reviews` | Search review history (`q`, filters, pagination) |
| `GET` | `/api/v1/reviews/{id}` | Analysis run details |
| `GET` | `/api/v1/reviews/{id}/report` | Export report (`format=markdown\|json\|summary`) |
| `GET` | `/api/v1/settings/me` | Current user settings |
| `PUT` | `/api/v1/settings/me` | Update user settings |
| `GET` | `/api/v1/settings/me/ollama-health` | Ollama status using user settings |
| `GET` | `/api/v1/health/ollama` | Global Ollama status (app defaults) |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/           # HTTP routes
│   │   ├── config/        # Settings
│   │   ├── db/            # Database session
│   │   ├── models/        # ORM models
│   │   ├── repositories/  # Data access
│   │   ├── schemas/       # Pydantic DTOs
│   │   ├── services/      # Business logic
│   │   ├── utils/         # Shared utilities
│   │   └── workers/       # Background tasks
│   ├── alembic/           # Database migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/           # HTTP client
│       ├── components/    # UI components
│       ├── hooks/         # React hooks
│       ├── pages/         # Route pages
│       └── routes/        # Router config
├── docs/
├── .github/workflows/     # CI pipelines
└── docker-compose.yml
```

## Roadmap

- [x] JWT authentication (register, login, refresh tokens)
- [x] GitHub repository cloning and URL validation
- [x] Multi-language static analysis (Python, JS/TS, Java, Go, Rust, C#, C++)
- [x] Ollama-powered structured AI reviews
- [x] Markdown, JSON, and summary reports
- [x] Review history and search
- [x] User settings (Ollama endpoint, model, ignored paths)
- [x] GitHub OAuth
- [ ] Pull request reviews
- [ ] Webhooks and team collaboration
- [ ] Background workers
- [ ] Vector search and RAG
- [ ] Repository chat

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit using [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, etc.)
4. Ensure CI passes (`ruff`, `mypy`, `pytest`, ESLint, tests, Docker build)
5. Open a pull request

## License

[MIT](LICENSE)
