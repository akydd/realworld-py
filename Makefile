.PHONY: int-tests lint start dev

start:
	docker compose up -d
	until docker compose exec -T db pg_isready -U admin -d app; do sleep 1; done
	uv run fastapi run app/main.py --port 8090

dev:
	docker compose up -d
	until docker compose exec -T db pg_isready -U admin -d app; do sleep 1; done
	uv run fastapi dev app/main.py --port 8090

lint:
	golangci-lint run ./...

int-tests:
	docker compose -f compose.test.yaml up -d
	until docker compose -f compose.test.yaml exec -T test_db pg_isready -U admin -d test-app; do sleep 1; done
	uv run --env-file .env_test uvicorn app.main:app --port 8097 & echo $$! > server.pid
	sleep 2
	HOST=http://localhost:8097 ../realworld/specs/api/run-api-tests-hurl.sh; \
	RESULT=$$?; \
	kill $$(cat server.pid) 2>/dev/null || true; \
	rm -f server.pid; \
	docker compose -f compose.test.yaml exec -T test_db psql -U admin -d test-app -c "TRUNCATE TABLE users CASCADE;"; \
	docker compose -f compose.test.yaml down; \
	exit $$RESULT
