.PHONY: test dev-backend dev-frontend lint docker-up docker-down seed-admin

test:
	cd backend && uv run --extra dev pytest -v

lint:
	cd backend && uv run --extra dev ruff check .

dev-backend:
	cd backend && uv run uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

seed-admin:
	cd backend && uv run python scripts/seed_admin.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
