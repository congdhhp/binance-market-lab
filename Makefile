.PHONY: help up down build logs shell migrate makemigrations createsuperuser test test-backend test-frontend ingest ingest-test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all Docker images
	docker compose build

rebuild: ## Rebuild all Docker images from scratch
	docker compose build --no-cache

logs: ## Show logs from all services
	docker compose logs -f

logs-backend: ## Show logs from backend service
	docker compose logs -f backend

logs-celery: ## Show logs from celery worker
	docker compose logs -f celery_worker

logs-beat: ## Show logs from celery beat
	docker compose logs -f celery_beat

shell: ## Open Django shell
	docker compose exec backend python backend/manage.py shell

dbshell: ## Open database shell
	docker compose exec db psql -U postgres -d binance_market_lab

redis-cli: ## Open Redis CLI
	docker compose exec redis redis-cli

migrate: ## Run database migrations
	docker compose exec backend python backend/manage.py migrate

makemigrations: ## Create new migrations
	docker compose exec backend python backend/manage.py makemigrations

createsuperuser: ## Create a Django superuser
	docker compose exec backend python backend/manage.py createsuperuser

collectstatic: ## Collect static files
	docker compose exec backend python backend/manage.py collectstatic --noinput

test: test-backend ## Run all tests

test-backend: ## Run backend tests
	docker compose exec backend pytest

test-coverage: ## Run tests with coverage
	docker compose exec backend pytest --cov=apps --cov-report=html

ingest: ## Trigger data ingestion for all symbols
	docker compose exec backend python backend/manage.py shell -c "from apps.market_data.tasks import ingest_all_symbols_klines; ingest_all_symbols_klines.delay('1h', 50)"

ingest-test: ## Test ingestion for BTC/USDT 1 day
	docker compose exec backend python backend/manage.py shell -c "from apps.market_data.tasks import ingest_klines_task; from datetime import datetime, timedelta; end = datetime.utcnow(); start = end - timedelta(days=1); ingest_klines_task('BTCUSDT', '1m', start, end)"

backfill: ## Backfill historical data (usage: make backfill SYMBOL=BTCUSDT INTERVAL=1h DAYS=30)
	docker compose exec backend python backend/manage.py shell -c "from apps.market_data.tasks import bulk_backfill_task; from datetime import datetime, timedelta; bulk_backfill_task.delay('$(SYMBOL)', '$(INTERVAL)', (datetime.utcnow() - timedelta(days=$(DAYS))).isoformat())"

check-quality: ## Run data quality check
	docker compose exec backend python backend/manage.py shell -c "from apps.market_data.tasks import data_quality_check; data_quality_check.delay()"

clean: ## Remove all containers, volumes, and images
	docker compose down -v
	docker system prune -af

restart: down up ## Restart all services

restart-backend: ## Restart backend service
	docker compose restart backend

restart-celery: ## Restart celery worker
	docker compose restart celery_worker

restart-beat: ## Restart celery beat
	docker compose restart celery_beat

ps: ## Show running containers
	docker compose ps

stats: ## Show container resource usage
	docker stats

format: ## Format Python code with black
	docker compose exec backend black backend/

lint: ## Lint Python code with flake8
	docker compose exec backend flake8 backend/

type-check: ## Run mypy type checking
	docker compose exec backend mypy backend/

install-dev: ## Install development dependencies
	docker compose exec backend pip install -r /app/requirements/dev.txt

flower: ## Start Celery Flower monitoring tool
	docker compose exec celery_worker celery -A config flower --port=5555

# Frontend specific commands
frontend-shell: ## Open frontend container shell
	docker compose exec frontend sh

frontend-install: ## Install frontend dependencies
	docker compose exec frontend npm install

frontend-build: ## Build frontend for production
	docker compose exec frontend npm run build

# Database backup and restore
backup-db: ## Backup database to file
	docker compose exec -T db pg_dump -U postgres binance_market_lab > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database from file (usage: make restore-db FILE=backup.sql)
	docker compose exec -T db psql -U postgres binance_market_lab < $(FILE)

# First time setup
setup: build up migrate createsuperuser ## Initial project setup
	@echo "Setup complete! Access the application at http://localhost:8000"
