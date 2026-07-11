# AI GitHub Code Reviewer

A production-oriented web application for analyzing GitHub repositories and pull requests using a local LLM via [Ollama](https://ollama.com). Everything runs locally with no paid API dependencies.

## Overview

AI GitHub Code Reviewer helps developers inspect code quality across multiple languages, surface issues with severity and confidence scores, and generate structured review reports. The application stores review history in PostgreSQL and provides a modern dashboard for browsing results.

**Current status:** Foundation and JWT authentication (Step 2) are implemented. Repository analysis and Ollama integration are on the roadmap.

## Screenshots

| Dashboard | Review History |
|-----------|----------------|
| ![Dashboard placeholder](docs/images/dashboard.png) | ![History placeholder](docs/images/history.png) |

> Screenshot placeholders — replace with actual captures once features are implemented.

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
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API base URL |

Copy `.env.example` to `.env` and adjust values for your environment.

## API Documentation

Interactive Swagger UI is available at `/docs` when the backend is running.

### Health endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Liveness check |
| `GET` | `/api/v1/ready` | Readiness check (includes database) |
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Sign in |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/auth/me` | Current user (Bearer token required) |

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
- [ ] GitHub repository cloning and URL validation
- [ ] Multi-language static analysis (Python, JS/TS, Java, Go, Rust, C#, C++)
- [ ] Ollama-powered structured AI reviews
- [ ] Markdown, JSON, and summary reports
- [ ] Review history and search
- [ ] User settings (Ollama endpoint, model, ignored paths)
- [ ] GitHub OAuth
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
