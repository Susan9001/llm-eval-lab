.PHONY: up down logs ps test lint fmt fix

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

test:
	cd backend && .venv/bin/pytest

lint:
	cd backend && .venv/bin/ruff check app tests

fmt:
	cd backend && .venv/bin/ruff format app tests

fix:
	cd backend && .venv/bin/ruff check --fix app tests
	cd backend && .venv/bin/ruff format app tests
