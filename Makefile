install:
	pip install -e ".[dev]"

migrate:
	alembic upgrade head

seed:
	python scripts/seed.py

api:
	uvicorn app.main:app --reload --app-dir backend

test:
	pytest
