.PHONY: test dev-backend dev-frontend lint docker-up docker-down

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

docker-up:
	docker compose up --build

docker-down:
	docker compose down
