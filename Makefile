.PHONY: up down logs ps test lint fmt

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

# 代码静态检查
lint:
	cd backend && .venv/bin/ruff check app tests

fmt:
	cd backend && .venv/bin/ruff format app tests
