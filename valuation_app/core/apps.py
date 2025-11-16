"""Core application configuration."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Business Valuation Core'
    
    def ready(self):
        """Import signals when the app is ready."""
        # Import signals if needed
        pass
