# Changelog

All notable changes to Binance Market Lab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Phase 2: Technical Analysis & Indicators Engine
- Phase 3: Backtesting Engine
- Phase 4: Orderbook Analytics & Risk Metrics
- Phase 5: Anomaly Detection (ML)
- Phase 6: React Dashboard & Notifications
- Phase 7: AI Forecasting & Sentiment Engine
- Phase 8: LLM Intelligence Layer

## [0.1.0] - 2026-02-16

### Added - Phase 0: Infrastructure ✅
- Django 5.0 project structure with settings split (base, development, production)
- Docker Compose orchestration for 6 services:
  - PostgreSQL 16 with TimescaleDB extension
  - Redis 7 for Celery broker and caching
  - Django backend with Gunicorn
  - Celery worker for async task processing
  - Celery beat for scheduled tasks
  - React frontend (skeleton)
- Celery configuration with automatic task discovery
- Celery Beat schedule for data ingestion tasks
- Comprehensive Makefile with 30+ convenience commands
- Environment variable management with django-environ
- CORS configuration for React frontend
- DRF Spectacular for API documentation
- Structured logging configuration

### Added - Phase 1: Data Ingestion Pipeline ✅
- **Django Models** (apps/market_data/):
  - `Symbol` - Trading pair metadata with trading rules
  - `Kline` - OHLCV candlestick data (hypertable)
  - `Trade` - Aggregated trade data (hypertable)
  - `OrderBookSnapshot` - Periodic orderbook depth (hypertable)
  - `Ticker24h` - 24-hour ticker statistics (hypertable)
  - `FundingRate` - Futures funding rates (hypertable)
  - `OpenInterest` - Futures open interest (hypertable)
  - `IngestionLog` - Data ingestion status tracking

- **TimescaleDB Hypertables**:
  - Automatic partitioning by time for all time-series tables
  - Compression policies (7 days for klines/trades, 3 days for orderbook)
  - Optimized indexes for time-range queries

- **Binance API Client** (services/binance_client.py):
  - Rate limiting decorator (1200 calls/minute)
  - Exponential backoff retry logic
  - Comprehensive error handling
  - Support for Spot and Futures endpoints
  - Methods for: klines, trades, orderbook, tickers, funding rates, open interest
  - Automatic pagination for historical data (get_historical_klines)

- **Celery Tasks** (apps/market_data/tasks.py):
  - `ingest_klines_task` - Fetch and store klines for a symbol
  - `ingest_all_symbols_klines` - Batch ingest for all tracked symbols
  - `ingest_trades_task` - Fetch aggregated trade data
  - `ingest_orderbook_snapshot` - Capture orderbook depth
  - `ingest_orderbook_snapshots` - Batch orderbook ingestion
  - `ingest_ticker_24h` - Fetch 24h ticker for all symbols
  - `ingest_funding_rates` - Fetch funding rates for all futures
  - `ingest_open_interest` - Fetch open interest data
  - `bulk_backfill_task` - Historical data backfill
  - `data_quality_check` - Detect gaps and trigger auto-backfill

- **Celery Beat Schedule**:
  - 1-minute klines: every minute (top 20 symbols)
  - 1-hour klines: hourly (top 100 symbols)
  - 4-hour klines: every 4 hours (top 100 symbols)
  - Daily klines: daily at midnight (top 200 symbols)
  - 24h tickers: every 5 minutes (all symbols)
  - Funding rates: every 8 hours (all futures)
  - Open interest: every 15 minutes (all futures)
  - Orderbook snapshots: every minute (top 10 symbols)
  - Data quality check: daily at 2 AM

- **REST API Endpoints** (DRF ViewSets):
  - `GET /api/v1/market-data/symbols/` - List/CRUD symbols
  - `GET /api/v1/market-data/klines/` - Query klines with time range filters
  - `GET /api/v1/market-data/klines/latest/` - Get latest kline for symbol
  - `GET /api/v1/market-data/trades/` - Query trade history
  - `GET /api/v1/market-data/orderbook/` - Query orderbook snapshots
  - `GET /api/v1/market-data/orderbook/latest/` - Get latest orderbook
  - `GET /api/v1/market-data/tickers/` - Query ticker history
  - `GET /api/v1/market-data/tickers/latest_all/` - Get latest tickers for all symbols
  - `GET /api/v1/market-data/funding-rates/` - Query funding rate history
  - `GET /api/v1/market-data/open-interest/` - Query open interest history
  - `POST /api/v1/market-data/ingest/backfill/` - Trigger manual historical backfill
  - `GET /api/v1/market-data/ingest/status/` - Check ingestion health status
  - `GET /api/health/` - Application health check

- **API Features**:
  - Filtering by symbol, interval, time range
  - Ordering by any field
  - Pagination (limit/offset, default 100 items)
  - Django-filter integration
  - OpenAPI schema with Swagger UI and ReDoc

- **Django Admin**:
  - Full admin interface for all models
  - Custom list displays with relevant fields
  - Filters, search, and date hierarchy
  - Editable inline fields (is_tracked, priority)
  - Ingestion log monitoring

### Configuration
- Requirements split (base.txt, dev.txt, prod.txt)
- Python 3.11 base image
- Development vs production settings
- Environment-based configuration
- Security settings for production

### Developer Experience
- Makefile commands for common operations
- Hot-reload for local development
- Docker volume mounts for code
- Comprehensive logging
- Health checks for all services
- Database backup/restore commands
- Test infrastructure (pytest)

### Documentation
- Comprehensive README with quick start guide
- Detailed implementation plan (PLAN.md) for all 8 phases
- API documentation at /api/docs/ (Swagger UI)
- Inline code documentation
- This changelog

### Migration Scripts
- 0001_initial.py - Create all database tables
- 0002_setup_timescaledb_hypertables.py - Convert to hypertables and add policies

### Scripts
- quickstart.sh - One-command setup script
- Makefile targets for all common operations

## [0.0.0] - 2026-02-16 (Initial Commit)
- Repository created with MIT license
- Python .gitignore template
