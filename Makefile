.PHONY: up down api-test web-check verify

up:
	docker compose up --build

down:
	docker compose down -v

api-test:
	cd backend && pytest

web-check:
	cd frontend && pnpm lint && pnpm test && pnpm build

verify: api-test web-check
	@echo "All local quality checks passed."
