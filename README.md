# Rag Platform

Backend-first RAG platform for document intelligence.

The long-term goal is to let users upload documents, extract content, index it, ask questions, and receive grounded answers with citations.

## Current Phase

Phase 00: Repository and execution baseline.

This phase only proves that the backend can run, test, lint, and boot consistently.

## Included

- FastAPI app
- Health endpoint
- Settings loader
- Pytest tests
- Ruff linting
- Dockerfile
- Docker Compose
- GitHub Actions CI

## Not Included Yet

- File upload
- PDF parsing
- Chunking
- Embeddings
- Vector database
- RAG
- Agent workflows
- Authentication
- Frontend

## Requirements

- Python 3.14.3

## Local Setup

```powershell
python --version
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run API

```powershell
uvicorn app.main:app --reload
```

Open:

```txt
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "app": "Rag Platform",
  "environment": "local",
  "version": "v1"
}
```

## Run Tests

```powershell
pytest -q
```

## Run Lint

```powershell
ruff check .
```

## Run With Docker

```powershell
docker compose up --build
```

## Phase 00 Definition of Done

Phase 00 is complete when:

- API boots locally
- `/health` returns `status: ok`
- `pytest -q` passes
- `ruff check .` passes
- Docker Compose runs the API
- GitHub Actions runs lint and tests
