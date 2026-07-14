.PHONY: up down logs build migrate makemigration seed shell-core shell-ai shell-deploy shell-inbox shell-analytics test fmt

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

build:
	docker compose build

migrate:
	docker compose run --rm core-api alembic upgrade head

makemigration:
	@read -p "Message: " msg; \
	docker compose run --rm core-api alembic revision --autogenerate -m "$$msg"

seed:
	docker compose run --rm core-api python -m app.scripts.seed

shell-core:
	docker compose exec core-api bash

shell-ai:
	docker compose exec ai-orchestrator bash

shell-deploy:
	docker compose exec deploy-service bash

shell-inbox:
	docker compose exec inbox-service bash

shell-analytics:
	docker compose exec analytics-service bash

test:
	docker compose run --rm core-api pytest
	docker compose run --rm ai-orchestrator pytest

fmt:
	docker compose run --rm core-api ruff format app && docker compose run --rm core-api ruff check --fix app
	docker compose run --rm ai-orchestrator ruff format app && docker compose run --rm ai-orchestrator ruff check --fix app
