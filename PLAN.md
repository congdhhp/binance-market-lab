# Binance Market Lab — Implementation Plan

> **Last updated**: 2026-02-16
> **Stack**: Django + DRF (backend), React + TypeScript (frontend), PostgreSQL + TimescaleDB, Celery + Redis, Docker Compose
> **Deployment**: Local/VPS + Docker Compose

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Phase 0: Scaffold & Infrastructure](#phase-0-scaffold--infrastructure-week-1)
- [Phase 1: Data Ingestion Pipeline](#phase-1-data-ingestion-pipeline-week-2-3)
- [Phase 2: Technical Analysis Engine](#phase-2-technical-analysis--indicators-engine-week-3-4)
- [Phase 3: Backtesting Engine](#phase-3-backtesting-engine-week-4-6)
- [Phase 4: Orderbook Analytics & Risk Metrics](#phase-4-orderbook-analytics--risk-metrics-week-5-7)
- [Phase 5: Anomaly Detection (ML)](#phase-5-anomaly-detection-ml-week-6-8)
- [Phase 6: React Dashboard & Notifications](#phase-6-react-dashboard--notifications-week-3-8-parallel)
- [Phase 7: AI Forecasting & Sentiment Engine](#phase-7-ai-forecasting--sentiment-engine-week-9-11)
- [Phase 8: LLM Intelligence Layer](#phase-8-llm-intelligence-layer-week-11-13)
- [Cross-cutting Concerns](#cross-cutting-concerns)
- [Timeline Overview](#timeline-overview)
- [Key Decisions](#key-decisions)
- [Verification & Testing](#verification--testing)
- [Binance API Endpoints Reference](#binance-api-endpoints-reference)
- [Common Pitfalls & Notes](#common-pitfalls--notes)

---

## Overview

Full-stack platform phân tích dữ liệu thị trường crypto sử dụng Binance API. Platform bao gồm:

- **Data ingestion pipeline**: thu thập OHLCV, trades, orderbook, tickers, funding rates, open interest
- **Technical analysis engine**: indicators, signal generation
- **Backtesting framework**: strategy replay, factor research
- **Orderbook analytics**: spread, imbalance, liquidity analysis
- **Risk metrics**: volatility, VaR, correlation, market regime detection
- **Anomaly detection**: ML-based unusual pattern detection
- **AI forecasting**: price direction prediction, sentiment analysis
- **LLM intelligence**: auto market reports, natural language query, ensemble signal combiner
- **Interactive dashboard**: React frontend với charts, heatmaps, screener, alerts

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend (Vite)                        │
│  Heatmap │ Charts │ Screener │ Backtest UI │ Chat │ Reports │ Alerts│
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API (JSON)
┌──────────────────────────────▼──────────────────────────────────────┐
│                     Django + DRF (Gunicorn)                         │
│  market_data │ analysis │ backtest │ orderbook │ alerts │ ai_*      │
└──────┬───────────┬───────────┬──────────────────────────────────────┘
       │           │           │
┌──────▼──────┐ ┌──▼────────┐ ┌▼──────────────┐
│  Celery     │ │  Redis    │ │  PostgreSQL   │
│  Worker +   │ │  Broker + │ │  + TimescaleDB│
│  Beat       │ │  Cache    │ │  (Hypertables)│
└──────┬──────┘ └───────────┘ └───────────────┘
       │
┌──────▼──────────────────┐
│  Binance API            │
│  REST + WebSocket       │
│  Spot + Futures         │
└─────────────────────────┘
```

---

## Project Structure

```
binance-market-lab/
├── backend/                      # Django project
│   ├── config/                   # Django settings, urls, wsgi, asgi
│   │   ├── settings/
│   │   │   ├── base.py           # Shared settings
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── celery.py             # Celery app config
│   │   └── wsgi.py / asgi.py
│   ├── apps/
│   │   ├── market_data/          # Data models, ingestion, API
│   │   ├── analysis/             # Technical analysis, indicators, risk, correlation
│   │   ├── backtest/             # Backtesting engine
│   │   ├── orderbook/            # Orderbook analytics
│   │   ├── alerts/               # Alert & notification system
│   │   ├── anomaly/              # Anomaly detection (ML)
│   │   ├── factors/              # Factor research lab
│   │   ├── ai_forecast/          # Price forecasting & sentiment
│   │   ├── sentiment/            # Sentiment analysis (NLP)
│   │   ├── ai_reports/           # LLM-generated market reports
│   │   └── chat/                 # Natural language query interface
│   ├── services/                 # Shared services
│   │   ├── binance_client.py     # Binance API wrapper
│   │   ├── websocket.py          # WebSocket consumer
│   │   └── cache.py              # Redis cache helpers
│   ├── tasks/                    # Celery tasks
│   ├── manage.py
│   └── requirements/
│       ├── base.txt
│       ├── dev.txt
│       └── prod.txt
├── frontend/                     # React app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/             # API client
│   │   └── store/                # State management (zustand)
│   ├── package.json
│   └── vite.config.ts
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docker-compose.yml            # All services
├── .env.example
├── Makefile                      # Shortcuts
├── PLAN.md                       # This file
└── README.md
```

---

## Phase 0: Scaffold & Infrastructure (Week 1)

### 0.1 — Docker Compose Setup

6 services:

| Service | Image | Purpose |
|---------|-------|---------|
| `db` | PostgreSQL 16 + TimescaleDB | Primary database |
| `redis` | Redis 7 | Celery broker + cache |
| `backend` | Django + Gunicorn | API server |
| `celery_worker` | Same as backend | Async task execution |
| `celery_beat` | Same as backend | Scheduled task scheduling |
| `frontend` | Node 20 (dev) / Nginx (prod) | React dashboard |

### 0.2 — Django Project Init

- Settings split: `base.py` / `development.py` / `production.py`
- Environment variables via `django-environ`
- CORS config for React frontend (`django-cors-headers`)

### 0.3 — TimescaleDB Setup

- Hypertable migrations for time-series data
- Compression policies (compress data older than 7 days)
- Retention policies (configurable, default keep all)

### 0.4 — Dependencies

**Backend** (`requirements/base.txt`):
```
django>=5.0
djangorestframework
psycopg[binary]
celery[redis]
django-celery-beat
python-binance
ccxt
pandas
numpy
ta
scikit-learn
django-cors-headers
django-filter
drf-spectacular
django-environ
structlog
```

**Frontend** (`package.json`):
```
react, typescript, vite, tailwindcss
recharts, lightweight-charts
@tanstack/react-query, axios
zustand, react-router-dom
```

### 0.5 — Makefile Shortcuts

```makefile
make up          # docker compose up -d
make down        # docker compose down
make migrate     # run migrations
make shell       # django shell
make test        # run all tests
make ingest      # trigger data ingestion
make logs        # tail all logs
```

---

## Phase 1: Data Ingestion Pipeline (Week 2-3)

### 1.1 — Django Models (`apps/market_data/`)

All time-series models use TimescaleDB hypertables:

| Model | Key Fields | Partitioned By |
|-------|-----------|----------------|
| `Symbol` | name, base_asset, quote_asset, status, listing_date | — |
| `Kline` | symbol, interval, open_time, O/H/L/C/V, quote_volume, trades_count | `open_time` |
| `Trade` | symbol, trade_id, price, quantity, timestamp, is_buyer_maker | `timestamp` |
| `OrderBookSnapshot` | symbol, timestamp, bids_json, asks_json, spread, mid_price | `timestamp` |
| `Ticker24h` | symbol, timestamp, price_change_pct, volume, high, low, weighted_avg_price | `timestamp` |
| `FundingRate` | symbol, timestamp, funding_rate, mark_price | `timestamp` |
| `OpenInterest` | symbol, timestamp, open_interest, open_interest_value | `timestamp` |
| `IngestionLog` | symbol, data_type, status, records_count, error_message, timestamp | — |

### 1.2 — Binance API Client (`services/binance_client.py`)

- Wrapper around `python-binance` with:
  - Rate limiting decorator
  - Retry logic (exponential backoff)
  - Error handling & logging
- Methods: `get_klines()`, `get_agg_trades()`, `get_order_book()`, `get_ticker_24h()`, `get_funding_rate()`, `get_open_interest()`
- Support both Spot and Futures endpoints
- Auto-handle pagination for historical bulk download

### 1.3 — Celery Tasks

| Task | Schedule | Scope |
|------|----------|-------|
| `ingest_klines_task(symbol, interval, start, end)` | On-demand / triggered | Single symbol |
| `ingest_all_symbols_klines()` | Every 1m (1m interval), hourly (1h), etc. | Top N symbols |
| `ingest_ticker_24h()` | Every 5 minutes | All symbols |
| `ingest_orderbook_snapshot(symbol)` | Every 10 seconds | Top 10 symbols |
| `ingest_funding_rates()` | Every 8 hours | All futures symbols |
| `ingest_open_interest()` | Every 15 minutes | Top 50 symbols |
| `bulk_backfill_task(symbol, interval, start_date)` | On-demand | Single symbol |
| `data_quality_check()` | Daily | All symbols |

### 1.4 — Data Quality & Validation

- Detect gaps in klines (missing candles)
- Auto-backfill gaps when detected
- Validate OHLCV consistency (high >= open, close, low)
- Track ingestion status per symbol in `IngestionLog`

### 1.5 — REST API Endpoints

```
GET  /api/v1/symbols/                    — List tracked symbols
GET  /api/v1/klines/{symbol}/            — Query klines (interval, start, end, limit)
GET  /api/v1/orderbook/{symbol}/         — Latest orderbook
GET  /api/v1/tickers/                    — All 24h tickers
GET  /api/v1/funding-rates/{symbol}/     — Funding rate history
POST /api/v1/ingest/backfill/            — Trigger manual backfill
GET  /api/v1/ingest/status/              — Ingestion health status
```

---

## Phase 2: Technical Analysis & Indicators Engine (Week 3-4)

### 2.1 — Indicator Computation Service (`apps/analysis/`)

`IndicatorService` class: receives DataFrame (klines) → computes all indicators.

**Indicators to implement:**

| Category | Indicators |
|----------|-----------|
| Trend | EMA (multiple periods), SMA, MACD, ADX, Ichimoku Cloud |
| Momentum | RSI, Stochastic Oscillator, Williams %R |
| Volatility | Bollinger Bands, ATR, Keltner Channels |
| Volume | VWAP, OBV (On Balance Volume), Volume Profile |
| Custom | Squeeze Momentum, Hull MA |

Uses `ta` library, wrapped for consistent interface.

### 2.2 — Pre-computed Indicators (Celery Task)

- After each kline ingestion, auto-compute common indicators
- Store in `IndicatorCache` hypertable: (symbol, interval, timestamp, indicator_name, value)
- Enables fast dashboard queries without re-computation

### 2.3 — Signal Generation Framework

| Model | Purpose |
|-------|---------|
| `SignalRule` | Define rules (e.g., "RSI < 30 AND MACD crossover") |
| `Signal` | Generated signals (symbol, timestamp, type, strength, rule_id) |

`SignalEngine`: evaluate rules against latest indicator values.

### 2.4 — REST API

```
GET  /api/v1/analysis/indicators/{symbol}/   — Computed indicators
GET  /api/v1/analysis/signals/               — List generated signals
POST /api/v1/analysis/compute/               — Trigger custom computation
```

---

## Phase 3: Backtesting Engine (Week 4-6)

### 3.1 — Strategy Framework (`apps/backtest/`)

```python
class Strategy(ABC):
    def on_candle(self, candle, indicators) -> Optional[Signal]: ...
    def on_signal(self, signal) -> Optional[Order]: ...
    def get_positions(self) -> List[Position]: ...
```

**Built-in strategies:**
1. MA Crossover (Golden Cross / Death Cross)
2. RSI Mean Reversion
3. Bollinger Band Breakout
4. Momentum Factor
5. VWAP Reversion
6. ATR Volatility Breakout

### 3.2 — Execution Simulator

- Slippage model: % of spread + volume impact
- Maker/taker fee modeling
- Funding rate costs for futures
- Simplified Almgren-Chriss market impact model

### 3.3 — Models

| Model | Key Fields |
|-------|-----------|
| `BacktestConfig` | strategy, symbols, timeframe, date range, capital, fees, slippage_model |
| `BacktestResult` | PnL curve, total_return, sharpe, sortino, max_drawdown, win_rate, profit_factor |
| `BacktestTrade` | entry/exit time, side, prices, quantity, pnl, fees |

### 3.4 — Factor Research Module (`apps/factors/`)

**Built-in factors:**
- Momentum (returns over N periods)
- Mean-reversion (z-score of returns)
- Volatility breakout (ATR ratio)
- Volume surge (volume vs rolling average)
- Liquidity score (spread + depth metrics)

`FactorBacktester`: cross-sectional factor testing on multiple symbols.
Output: factor returns, IC (Information Coefficient), turnover, factor-weighted portfolio performance.

### 3.5 — REST API

```
POST /api/v1/backtest/run/                — Submit backtest
GET  /api/v1/backtest/{id}/               — Get results
GET  /api/v1/backtest/{id}/trades/        — Get trade log
GET  /api/v1/backtest/{id}/equity-curve/  — Equity curve data
GET  /api/v1/factors/                     — List factors
POST /api/v1/factors/backtest/            — Run factor research
```

---

## Phase 4: Orderbook Analytics & Risk Metrics (Week 5-7)

### 4.1 — Orderbook Analytics (`apps/orderbook/`)

`OrderbookAnalyzer` computes:
- Bid-ask spread (absolute & relative)
- Mid price
- Book imbalance ratio (bid_depth / total_depth)
- Depth at N levels
- Cumulative depth chart data
- Liquidity holes detection (gaps > threshold)
- VWAP execution price estimation for given order size

`ImbalanceAlert`: triggered when buy_depth/sell_depth > configurable threshold.

### 4.2 — Volatility & Risk Metrics (`apps/analysis/risk.py`)

| Metric | Description |
|--------|------------|
| Realized Volatility | Rolling window (1h, 4h, 1d, 7d, 30d) |
| Value-at-Risk (VaR) | Historical, Parametric, Monte Carlo methods |
| Expected Shortfall (CVaR) | Conditional VaR |
| Maximum Drawdown | Depth, duration, recovery time |
| Sharpe / Sortino / Calmar | Risk-adjusted return ratios |
| Position sizing | Kelly criterion, fixed fractional, risk-budget based |

### 4.3 — Cross-Asset Correlation (`apps/analysis/correlation.py`)

- Rolling correlation matrix (configurable window: 7d, 30d, 90d)
- PCA analysis for dimensionality reduction
- Correlation regime change detection
- Heatmap data export for frontend

### 4.4 — Market Regime Detection

- Hidden Markov Model (HMM) with 3-4 states:
  - **Trending Up**: positive drift, moderate vol
  - **Trending Down**: negative drift, elevated vol
  - **Ranging**: near-zero drift, low vol
  - **High Volatility**: extreme vol, no clear direction
- Features: returns, volatility, volume ratio
- Output: current regime per symbol, transition probabilities

### 4.5 — REST API

```
GET /api/v1/orderbook/analysis/{symbol}/  — Orderbook metrics
GET /api/v1/risk/metrics/{symbol}/        — Risk metrics
GET /api/v1/correlation/matrix/           — Correlation data
GET /api/v1/regime/{symbol}/              — Current market regime
```

---

## Phase 5: Anomaly Detection (ML) (Week 6-8)

### 5.1 — Detection Models (`apps/anomaly/`)

| Model | Method | Detects |
|-------|--------|---------|
| Volume Anomaly | Isolation Forest | Pump signals, unusual volume spikes |
| Orderbook Anomaly | Statistical + IF | Spoofing patterns, unusual depth |
| Price Anomaly | LSTM Autoencoder | Sudden moves without catalyst |
| Multi-feature | Ensemble | Combined signals across all dimensions |

### 5.2 — ML Pipeline

- `ModelTrainer` Celery task: periodic retrain on rolling window data
- Feature store: pre-computed features in TimescaleDB
- Model versioning: save artifacts (joblib/pickle) with metadata
- `AnomalyScore` model: timestamp, symbol, model_name, score, is_anomaly, features_snapshot

### 5.3 — REST API

```
GET  /api/v1/anomaly/scores/{symbol}/     — Anomaly scores timeline
GET  /api/v1/anomaly/alerts/              — Flagged anomalies
POST /api/v1/anomaly/retrain/             — Trigger model retrain
GET  /api/v1/anomaly/models/              — Model performance stats
```

---

## Phase 6: React Dashboard & Notifications (Week 3-8, parallel)

### 6.1 — Dashboard Pages

| Page | Description |
|------|------------|
| **Overview/Home** | Market summary cards, top movers table, BTC dominance, total volume |
| **Heatmap** | Treemap visualization of % change by market cap, color-coded |
| **Symbol Detail** | Interactive candlestick chart (lightweight-charts), indicator overlays, volume, orderbook depth |
| **Screener** | Filterable table: price, change%, volume, RSI, volatility, anomaly score |
| **Backtest Lab** | Configure & run backtests, equity curve, trade log, metrics |
| **Factor Research** | Factor performance charts, IC over time, factor correlation |
| **Correlation Matrix** | Interactive heatmap, drill-down pair |
| **Orderbook Viewer** | Real-time depth chart, imbalance indicator, spread history |
| **Alerts** | Notification center, alert history, alert configuration |
| **Settings** | Manage tracked symbols, ingestion schedule, API keys |
| **Forecast** *(Phase 7)* | Directional forecast, confidence gauge, accuracy history |
| **Sentiment** *(Phase 7)* | Sentiment heatmap, news feed, sentiment vs price overlay |
| **AI Reports** *(Phase 8)* | Report list, markdown render, on-demand generation |
| **Chat** *(Phase 8)* | NL query interface, conversation history, inline charts |

### 6.2 — Frontend Architecture

- **State**: `zustand` for global state (selected symbol, timeframe, theme)
- **Server state**: `@tanstack/react-query` for API caching & refetching
- **Charts**: `recharts` for basic charts, `lightweight-charts` for candlestick
- **Styling**: `tailwindcss`, dark/light theme toggle
- **Layout**: Responsive (desktop-first, tablet-usable)

### 6.3 — Web Notification System

- Polling-based: React Query refetch alerts endpoint every 30s
- Toast notifications for new alerts (volume spike, anomaly, signal)
- Notification center: list all alerts, mark read/unread, filter by type
- `Alert` model (backend): alert_type, symbol, message, severity, timestamp, is_read
- Celery task: evaluate alert conditions → create Alert records

---

## Phase 7: AI Forecasting & Sentiment Engine (Week 9-11)

### 7.1 — Price Direction Forecasting (`apps/ai_forecast/`)

**Models:**

| Model | Key Fields |
|-------|-----------|
| `ForecastModel` | model_name, model_type, version, trained_at, metrics_json, status |
| `Forecast` | symbol, timestamp, horizon (1h/4h/1d), predicted_direction, confidence, actual_direction |
| `FeatureSet` | symbol, timestamp, features_json (pre-computed feature vector) |

**Feature engineering** (~40-60 features per sample):
- Price features: returns (multi-horizon), log returns, volatility, momentum
- Volume features: volume ratio, OBV change, volume profile
- Technical: RSI, MACD histogram, BB position, ATR ratio
- Orderbook: imbalance, spread, depth ratio
- Cross-asset: BTC correlation rolling, ETH correlation
- Regime: current HMM state
- Temporal: hour of day, day of week (cyclical encoding)

**Model progression:**
1. **LightGBM/XGBoost** (baseline) — tabular features → classify direction. Fast, interpretable (SHAP). ~55-60% accuracy for 4h direction.
2. **Temporal Fusion Transformer (TFT)** — multi-horizon, attention-based. Uses `pytorch-forecasting`.
3. **Ensemble** — weighted average, calibrated probability.

**Training pipeline:**
- Walk-forward: train 6 months, validate 1 month, test 1 month
- Retrain weekly with sliding window
- Track performance decay → auto trigger retrain
- Artifacts stored on filesystem/S3

**Anti-overfitting:**
- Purged cross-validation (no data leakage)
- Embargo period between train/test
- Feature importance tracking
- Out-of-sample monitoring

**REST API:**
```
GET  /api/v1/forecast/{symbol}/           — Latest forecasts (all horizons)
GET  /api/v1/forecast/{symbol}/history/   — Forecast history + accuracy
GET  /api/v1/forecast/models/             — Models & performance
POST /api/v1/forecast/retrain/            — Trigger retrain
```

### 7.2 — Sentiment Analysis Engine (`apps/sentiment/`)

**Data sources:**
- CryptoPanic API (free tier): aggregated crypto news
- RSS feeds: CoinDesk, CoinTelegraph, The Block, Decrypt
- Social signals: LunarCrush API or Reddit r/cryptocurrency
- Ingestion: every 15min (news), every 1h (social)

**Models:**

| Model | Key Fields |
|-------|-----------|
| `NewsArticle` | source, title, content_snippet, url, published_at, symbols_mentioned |
| `SentimentScore` | article_id, model_name, score (-1 to 1), label |
| `AggregatedSentiment` | symbol, timestamp, avg_score, article_count, social_volume, momentum |

**NLP pipeline:**
- **Primary**: FinBERT (`ProsusAI/finbert`) — local, free, financial-domain
- **Secondary**: LLM API (OpenAI/Anthropic) for high-quality critical analysis
- Entity extraction: map articles → symbols (NER or keyword matching)

**Aggregation:**
- Rolling sentiment per symbol (4h, 24h, 7d windows)
- Sentiment momentum (rate of change)
- Sentiment divergence (sentiment ≠ price direction → contrarian signal)
- Feeds into forecast feature set

**REST API:**
```
GET /api/v1/sentiment/{symbol}/           — Aggregated sentiment timeline
GET /api/v1/sentiment/news/               — Latest news + scores
GET /api/v1/sentiment/overview/           — Market-wide sentiment heatmap
```

---

## Phase 8: LLM Intelligence Layer (Week 11-13)

### 8.1 — Auto Market Reports (`apps/ai_reports/`)

**Report types:**
1. **Daily Market Digest**: top movers, volume changes, regime shifts, anomalies, correlations
2. **Symbol Deep Dive**: full analysis for 1 symbol (on-demand)
3. **Weekly Strategy Report**: backtest performance, factor returns, portfolio suggestions

**Implementation:**
- `ReportGenerator` service: collect data → build structured prompt → call LLM
- LLM options: OpenAI API (GPT-4o) or local Ollama (Llama 3, Qwen)
- Prompt templates: Jinja2, inject data context
- `Report` model: report_type, generated_at, content_markdown, data_snapshot_json
- Celery scheduled: daily digest at 00:00 UTC
- Quality: cross-reference LLM numbers with actual data, user feedback loop

**REST API:**
```
GET  /api/v1/reports/                     — List reports
GET  /api/v1/reports/{id}/                — Full report
POST /api/v1/reports/generate/            — On-demand generation
GET  /api/v1/reports/daily-digest/latest/ — Latest digest
```

### 8.2 — Natural Language Query (Chat with Data) (`apps/chat/`)

**Architecture:**
- User sends natural language question
- LLM (function calling) translates to SQL queries / API calls / visualization specs
- Response: text + optional chart data + data table

| Model | Purpose |
|-------|---------|
| `ChatSession` | user, created_at |
| `ChatMessage` | session, role, content, tool_calls_json, data_response_json |

- `QueryExecutor`: safely execute generated SQL (read-only, parameterized, 5s timeout)
- Schema context provided to LLM for accurate query generation

**Example queries:**
- "So sánh volatility BTC vs ETH trong 30 ngày qua"
- "Top 5 coins có volume tăng mạnh nhất hôm nay"
- "Correlation giữa BTC và SOL đang thay đổi thế nào?"
- "Chạy backtest RSI mean-revert trên ETH 3 tháng gần nhất"
- "Sentiment BTC tuần này so với tuần trước?"

**REST API:**
```
POST /api/v1/chat/                        — Send message, get response
GET  /api/v1/chat/sessions/               — List sessions
GET  /api/v1/chat/sessions/{id}/          — Full conversation
```

### 8.3 — AI Ensemble Signal Combiner (Meta-Model)

Combines ALL signals into unified score per symbol.

**Input signals:**
- Technical signals (Phase 2)
- Forecast output (Phase 7.1)
- Sentiment score (Phase 7.2)
- Anomaly score (Phase 5)
- Market regime (Phase 4)
- Risk metrics (Phase 4)
- Orderbook imbalance (Phase 4)

**Meta-model:** LightGBM stacking on signal features.

**Output:**
- `EnsembleSignal`: symbol, timestamp, conviction_score (-1 to 1), suggested_action (strong_sell → strong_buy), confidence, component_scores_json

**REST API:**
```
GET /api/v1/signals/ensemble/{symbol}/    — Latest ensemble signal
GET /api/v1/signals/ensemble/top/         — Top conviction symbols
```

---

## Cross-cutting Concerns

### API Documentation
- `drf-spectacular` → auto-gen OpenAPI schema
- Swagger UI at `/api/docs/`
- ReDoc at `/api/redoc/`

### Testing

| Layer | Tools | Scope |
|-------|-------|-------|
| Backend unit | `pytest` + `factory-boy` | Models, services, indicator calculations |
| Backend integration | `pytest` + mock Binance API | Full ingestion → analysis pipeline |
| Backtest engine | `pytest` | Strategy execution, PnL calculation |
| Frontend unit | `vitest` + `testing-library/react` | Component rendering, hooks |
| E2E | Manual / Playwright (optional) | Full user flows |

### Logging & Monitoring
- Structured logging: `structlog`
- Celery task monitoring: Flower (optional Docker service)
- Health check: `GET /api/health/`

### Security
- Binance API keys: read-only, stored in env vars
- Django auth for dashboard access
- Rate limiting on API endpoints
- SQL sandboxing for chat queries (read-only connection)

---

## Timeline Overview

| Phase | Scope | Week | Dependencies |
|-------|-------|------|-------------|
| **0** | Scaffold & Infrastructure | 1 | — |
| **1** | Data Ingestion Pipeline | 2-3 | Phase 0 |
| **2** | Technical Analysis Engine | 3-4 | Phase 1 |
| **3** | Backtesting Engine | 4-6 | Phase 1, 2 |
| **4** | Orderbook, Risk, Correlation | 5-7 | Phase 1 |
| **5** | Anomaly Detection (ML) | 6-8 | Phase 1, 4 |
| **6** | React Dashboard & Notifications | 3-8 (parallel) | Phase 1+ |
| **7** | AI Forecasting & Sentiment | 9-11 | Phase 1-5 |
| **8** | LLM Intelligence Layer | 11-13 | Phase 2-7 |

```
Week:  1    2    3    4    5    6    7    8    9   10   11   12   13
       ├─0──┤
            ├──1──────┤
                 ├──2──────┤
                      ├──3──────────────┤
                           ├──4──────────────┤
                                ├──5──────────────┤
                 ├──────────6 (parallel)─────────┤
                                                  ├──7──────────┤
                                                       ├──8──────────┤
```

---

## Key Decisions

| Decision | Chosen | Rationale |
|----------|--------|-----------|
| Backend framework | Django + DRF | Powerful ORM, admin, mature ecosystem |
| Frontend | React + TypeScript + Vite | Flexible UI, rich charting libraries |
| Database | PostgreSQL + TimescaleDB | SQL-native, time-series optimized, Django-compatible |
| Task queue | Celery + Redis | Mature, periodic tasks via Beat, widely supported |
| Alerts | Web notifications (polling) | Simple MVP, upgradeable to WebSocket later |
| Charting | lightweight-charts + recharts | TradingView quality candlesticks + general charts |
| ML baseline | LightGBM before Transformer | Fast, interpretable, competitive baseline |
| Sentiment NLP | FinBERT local | Free, privacy, domain-specific |
| LLM | OpenAI API + optional Ollama | Flexibility: cloud for quality, local for cost |
| Chat query | Function calling over RAG | Structured data → SQL more accurate than RAG |
| Deployment | Docker Compose | Self-hosted, full control, low cost |

### Deferred

| Feature | Reason |
|---------|--------|
| RL for Strategy Optimization | Training unstable, overfitting risk, needs mature infra |
| Chart Pattern Recognition (CV) | Needs large labeled dataset, academic evidence weak |
| WebSocket push to frontend | Polling sufficient for MVP, add later if needed |
| Telegram alerts | Web-only for now, easy to add channel later |

---

## Verification & Testing

| Test | Command | Validates |
|------|---------|-----------|
| Unit tests (backend) | `make test-backend` | Models, services, calculations |
| Unit tests (frontend) | `make test-frontend` | Components, hooks |
| Data pipeline | `make ingest-test` | Ingest 1 symbol/1 day → verify DB count (1440 for 1m) |
| Indicator accuracy | Manual comparison | Output vs TradingView for same symbol/timeframe |
| Backtest correctness | `pytest` | MACrossover on BTC/USDT → PnL matches manual calc |
| Docker health | `docker compose up` | All 6 services start, frontend loads, API responds |
| E2E flow | Manual | Backfill → dashboard shows data → run backtest → view results |

---

## Binance API Endpoints Reference

| Endpoint | Data | Use Case |
|----------|------|----------|
| `GET /api/v3/klines` | OHLCV candles | Technical analysis, backtest |
| `GET /api/v3/aggTrades` | Aggregated trades | Tick-level analysis, microstructure |
| `GET /api/v3/depth` | Order book | Spread, imbalance, liquidity |
| `GET /api/v3/ticker/24hr` | 24h ticker stats | Heatmap, screener |
| `GET /api/v3/avgPrice` | Average price | Quick reference |
| `GET /fapi/v1/klines` | Futures OHLCV | Futures backtest |
| `GET /fapi/v1/fundingRate` | Funding rates | Perpetual swap costs |
| `GET /fapi/v1/openInterest` | Open interest | Sentiment, positioning |
| `wss://stream.binance.com` | WebSocket streams | Real-time klines, trades, depth |
| Historical CSV archive | Bulk historical data | Large-scale backtest |

---

## Common Pitfalls & Notes

1. **Survivorship bias**: Track delistings, don't backtest only currently-listed symbols
2. **Timezone alignment**: Binance returns UTC timestamps — normalize all data to UTC
3. **Slippage & fees**: Crypto has wide spreads during low liquidity — model realistically
4. **Funding rates**: Must account for funding when backtesting perpetual futures
5. **Rate limits**: Binance enforces strict rate limits — use bulk download for history, throttle requests
6. **Data gaps**: Exchange downtime causes missing candles — detect and handle gracefully
7. **Look-ahead bias**: Never use future data in feature computation — strict temporal ordering
8. **Overfitting**: Use walk-forward validation, embargo periods, out-of-sample testing
9. **Token precision**: Different symbols have different tick sizes and lot sizes — respect trading rules
10. **API key security**: Use read-only keys only, never commit to git, store in env vars
