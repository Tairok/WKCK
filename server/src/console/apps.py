from django.apps import AppConfig
from pathlib import Path


class ConsoleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "console"
    path = str(Path(__file__).resolve().parent)
    
    def ready(self):
        """Initialize app - log startup"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("[STARTUP] BMC Console app initialized")
