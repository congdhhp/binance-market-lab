"""
Development settings for binance-market-lab project.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# CORS settings for React frontend
CORS_ALLOW_ALL_ORIGINS = True  # For development only
CORS_ALLOW_CREDENTIALS = True

# Logging - more verbose in development
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['celery']['level'] = 'DEBUG'

# Django Extensions (optional - install via dev.txt)
try:
    import django_extensions  # noqa
    INSTALLED_APPS += ['django_extensions']
except ImportError:
    pass
