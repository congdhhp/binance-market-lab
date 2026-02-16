from django.apps import AppConfig


class MarketDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.market_data'
    verbose_name = 'Market Data'

    def ready(self):
        """Import signal handlers when app is ready."""
        pass
