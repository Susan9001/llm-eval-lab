# llm-eval-lab

Evaluation lab for LLM quality and safety. Python + FastAPI + PostgreSQL + Redis, build for offline metrics, regression gating, and reporting.

## Tech stack

- Python (backend services)
- PostgreSQL (evaluation metadata and results)
- Redis (caching and task queue)
- Docker and Docker Compose (local orchestration)

## Project structure

```text
llm-eval-lab/
  backend/
    app/
      configs/
      datasets/
      models/
      services/
        dataset_loader.py
        prompt_runner.py
        model_adapters/
        judges/
        aggregator.py
        reporter.py
        regression.py
      api/
      workers/
    tests/
  data/
    snapshots/
  prompts/
    truthfulness/
    safety/
  reports/
  docker-compose.yml
  README.md
```

## Getting started

1. Start PostgreSQL and Redis with Docker

   ```bash
   docker compose up -d
   ```

2. Create and activate a Python virtual environment (from `backend`)

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```

3. Install initial dependencies

   ```bash
   pip install sqlalchemy psycopg2-binary python-dotenv pytest ruff
   ```

4. Run the smoke tests

   ```bash
   pytest
   ```

Later, as more features are implemented, docs will be added with:

- Evaluation pipeline description
- API usage
- Example reports
