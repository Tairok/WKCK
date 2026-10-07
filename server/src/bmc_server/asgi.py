import os
import logging
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmc_server.settings")

application = get_asgi_application()

# Initialize sensor polling service
logger = logging.getLogger(__name__)
try:
    from services.ohm_poller_service import OHMPollerService
    OHMPollerService.start()
    logger.info("OHM Poller Service started")
except Exception as e:
    logger.warning(f"Could not start OHM Poller Service: {e}")

