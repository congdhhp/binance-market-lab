"""
Celery configuration for binance-market-lab project.
"""
import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('binance_market_lab')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule
app.conf.beat_schedule = {
    # Klines ingestion - 1 minute interval for top symbols
    'ingest-1m-klines': {
        'task': 'apps.market_data.tasks.ingest_all_symbols_klines',
        'schedule': crontab(minute='*/1'),  # Every minute
        'kwargs': {'interval': '1m', 'limit': 20}
    },
    # Klines ingestion - 1 hour interval
    'ingest-1h-klines': {
        'task': 'apps.market_data.tasks.ingest_all_symbols_klines',
        'schedule': crontab(minute=0),  # Every hour
        'kwargs': {'interval': '1h', 'limit': 100}
    },
    # Klines ingestion - 4 hour interval
    'ingest-4h-klines': {
        'task': 'apps.market_data.tasks.ingest_all_symbols_klines',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'kwargs': {'interval': '4h', 'limit': 100}
    },
    # Klines ingestion - 1 day interval
    'ingest-1d-klines': {
        'task': 'apps.market_data.tasks.ingest_all_symbols_klines',
        'schedule': crontab(minute=0, hour=0),  # Daily at midnight
        'kwargs': {'interval': '1d', 'limit': 200}
    },
    # 24h ticker snapshot
    'ingest-ticker-24h': {
        'task': 'apps.market_data.tasks.ingest_ticker_24h',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    # Funding rates
    'ingest-funding-rates': {
        'task': 'apps.market_data.tasks.ingest_funding_rates',
        'schedule': crontab(minute=0, hour='*/8'),  # Every 8 hours
    },
    # Open interest
    'ingest-open-interest': {
        'task': 'apps.market_data.tasks.ingest_open_interest',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    # Orderbook snapshot for top 10 symbols
    'ingest-orderbook-snapshot': {
        'task': 'apps.market_data.tasks.ingest_orderbook_snapshots',
        'schedule': crontab(minute='*'),  # Every minute
        'kwargs': {'limit': 10}
    },
    # Data quality check
    'data-quality-check': {
        'task': 'apps.market_data.tasks.data_quality_check',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
