# Binance Market Lab 🚀

**Full-stack cryptocurrency market data analysis platform** powered by Binance API, Django, React, and AI.

## 🎯 Project Overview

A comprehensive platform for crypto market analysis featuring:
- Real-time data ingestion from Binance (OHLCV, trades, orderbook, tickers, funding rates, OI)
- Technical analysis with 15+ indicators
- Backtesting engine with multiple strategies
- Orderbook analytics & risk metrics
- ML-based anomaly detection
- AI price forecasting & sentiment analysis
- LLM-powered market reports & natural language queries
- Interactive React dashboard with TradingView-quality charts

## 📊 Current Status: Phase 1 Complete ✅

### ✅ Phase 0: Infrastructure (Complete)
- [x] Django project structure with settings split (dev/prod)
- [x] Docker Compose setup (PostgreSQL + TimescaleDB, Redis, Django, Celery, React)
- [x] Celery with Redis broker & beat scheduler
- [x] Makefile with 30+ convenience commands
- [x] Environment configuration

### ✅ Phase 1: Data Ingestion Pipeline (Complete)
- [x] Django models for all market data types (Symbol, Kline, Trade, OrderBook, Ticker24h, FundingRate, OpenInterest)
- [x] TimescaleDB hypertables for time-series data
- [x] Binance API client with rate limiting, retry logic, error handling
- [x] Celery tasks for data ingestion (klines, trades, orderbook, tickers, funding rates, open interest)
- [x] Scheduled ingestion with Celery Beat
- [x] Data quality validation & gap detection with auto-backfill
- [x] REST API endpoints (DRF) with filtering, pagination, ordering
- [x] Django admin interface for all models

### 🚧 Coming Next: Phase 2-8
See [PLAN.md](PLAN.md) for detailed implementation timeline.

## 🏗️ Architecture

```
Frontend (React + Vite)
         ↓ REST API
Backend (Django + DRF + Gunicorn)
    ↓           ↓
Celery      TimescaleDB
Worker      (PostgreSQL)
    ↓
Redis
    ↓
Binance API
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/congdhhp/binance-market-lab.git
cd binance-market-lab

# Copy environment file
cp .env.example .env

# Edit .env and add your Binance API keys (READ-ONLY recommended)
nano .env

# Build and start all services
make up

# Run database migrations & create TimescaleDB hypertables
make migrate

# Create admin user
make createsuperuser

# Check logs
make logs
```

The application will be available at:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs/
- **Django Admin**: http://localhost:8000/admin/
- **Frontend** (Phase 6): http://localhost:5173

### Initial Data Setup

```bash
# Add tracked symbols to database (via Django admin or shell)
make shell
>>> from apps.market_data.models import Symbol
>>> Symbol.objects.create(name='BTCUSDT', base_asset='BTC', quote_asset='USDT', is_tracked=True, priority=100)
>>> Symbol.objects.create(name='ETHUSDT', base_asset='ETH', quote_asset='USDT', is_tracked=True, priority=90)
>>> exit()

# Trigger manual backfill for historical data (e.g., BTC 30 days)
make backfill SYMBOL=BTCUSDT INTERVAL=1h DAYS=30

# Or use the test ingestion command
make ingest-test
```

## 📡 API Endpoints (Phase 1)

### Market Data
- `GET /api/v1/market-data/symbols/` - List all symbols
- `GET /api/v1/market-data/klines/?symbol_name=BTCUSDT&interval=1h&start_time=...&end_time=...` - Query klines
- `GET /api/v1/market-data/klines/latest/?symbol_name=BTCUSDT&interval=1h` - Latest kline
- `GET /api/v1/market-data/orderbook/?symbol_name=BTCUSDT` - Orderbook snapshots
- `GET /api/v1/market-data/orderbook/latest/?symbol_name=BTCUSDT` - Latest orderbook
- `GET /api/v1/market-data/tickers/` - All 24h tickers
- `GET /api/v1/market-data/tickers/latest_all/` - Latest ticker for all tracked symbols
- `GET /api/v1/market-data/funding-rates/?symbol_name=BTCUSDT` - Funding rate history
- `GET /api/v1/market-data/open-interest/?symbol_name=BTCUSDT` - Open interest history
- `POST /api/v1/market-data/ingest/backfill/` - Trigger manual backfill
- `GET /api/v1/market-data/ingest/status/` - Ingestion health status

Full API documentation with interactive Swagger UI: http://localhost:8000/api/docs/

## 🎛️ Makefile Commands

```bash
make help              # Show all available commands
make up                # Start all services
make down              # Stop all services
make build             # Build Docker images
make logs              # View logs from all services
make shell             # Open Django shell
make dbshell           # Open PostgreSQL shell
make migrate           # Run migrations
make makemigrations    # Create new migrations
make test              # Run tests
make ingest-test       # Test data ingestion
make backfill          # Backfill historical data
make clean             # Remove all containers & volumes
```

## 🗂️ Project Structure

```
binance-market-lab/
├── backend/                    # Django backend
│   ├── apps/
│   │   └── market_data/        # ✅ Phase 1: Market data models, tasks, API
│   ├── config/                 # Django settings, URLs, Celery config
│   ├── services/               # Binance API client
│   └── requirements/           # Python dependencies
├── frontend/                   # React frontend (Phase 6)
├── docker/                     # Dockerfiles
├── docker-compose.yml          # Service orchestration
├── Makefile                    # Convenience commands
├── .env                        # Environment variables
├── PLAN.md                     # Detailed implementation plan
└── README.md                   # This file
```

## 📚 Technologies

### Backend
- **Django 5.0** - Web framework
- **Django REST Framework** - REST API
- **PostgreSQL 16 + TimescaleDB** - Time-series database
- **Celery + Redis** - Async task queue & scheduling
- **python-binance** - Binance API client

### Frontend (Phase 6)
- **React 18 + TypeScript** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **lightweight-charts** - TradingView-quality charts
- **React Query** - Server state management

### AI/ML (Phase 7-8)
- **LightGBM / XGBoost** - Forecasting models
- **PyTorch + Transformers** - NLP & sentiment analysis
- **OpenAI API** - LLM for reports & chat

## 📖 Documentation

- **Implementation Plan**: [PLAN.md](PLAN.md) - Complete phase-by-phase plan (9 phases, 13 weeks)
- **API Docs**: http://localhost:8000/api/docs/ - Interactive Swagger UI
- **Django Admin**: http://localhost:8000/admin/ - Database admin interface

## 🔐 Security Notes

- Use **READ-ONLY** Binance API keys for data ingestion
- Never commit `.env` file to version control (already in .gitignore)
- Change `SECRET_KEY` in production
- Enable SSL and proper authentication before exposing to internet

## 🐛 Development

### Running Tests
```bash
make test              # Run all tests
make test-coverage     # Run tests with coverage report
```

### Code Quality
```bash
make format            # Format code with black
make lint              # Lint with flake8
make type-check        # Type checking with mypy
```

### Database Operations
```bash
make dbshell           # PostgreSQL shell
make backup-db         # Backup database
make restore-db FILE=backup.sql  # Restore database
```

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome! Open an issue or discussion.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 👨‍💻 Author

**Cong Do Hong** ([@congdhhp](https://github.com/congdhhp))

---

⚡ **Status**: Phase 1 Complete | Next: Phase 2 (Technical Analysis Engine)  
📅 **Last Updated**: 2026-02-16