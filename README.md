# llm-eval-lab

Evaluation lab for LLM quality and safety. Python + FastAPI + PostgreSQL + Redis, build for offline metrics, regression gating, and reporting.

## Tech stack

- Python (backend services)
- PostgreSQL (evaluation metadata and results)
- Redis (caching and task queue)
- Docker and Docker Compose (local orchestration)

## Dependencies

```bash
PYTHONPATH=backend pip install -r backend/requirements-dev.txt
```

## Quickstart

CLIs to generate model outputs and run eval can be found in `docs/`.

### Run tests

From repo root:

```bash
make test
```

