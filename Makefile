.PHONY: install dev test lint format docker-up docker-down

install:
	pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload

test:
	pytest -q

lint:
	ruff check .

format:
	ruff check . --fix
	ruff format .

docker-up:
	docker compose up --build

docker-down:
	docker compose down