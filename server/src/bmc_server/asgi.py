import os
import logging
import sys
import warnings
from django.core.asgi import get_asgi_application

# Silence Python warnings (e.g. from pythonnet/qrcode) so the console stays readable
warnings.filterwarnings("ignore")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmc_server.settings")

# Print startup banner
print("\n" + "="*60)
print("🚀 LOCAL SYSTEM MONITOR STARTING UP...")
print("="*60)

application = get_asgi_application()

# Initialize sensor polling service
logger = logging.getLogger(__name__)
try:
    from services.sensor_service import SensorService
    SensorService.start()
    logger.info("Sensor Service started")
    print("✅ Hardware sensor polling: RUNNING")
except Exception as e:
    logger.warning(f"Could not start OHM Poller Service: {e}")
    print(f"⚠️  Hardware sensor polling: FAILED - {e}")

# Print server ready message
print("✅ System Monitor Server: READY")
print("📊 Dashboard: http://127.0.0.1:8000")
print("🔍 Status Check: http://127.0.0.1:8000/api/status")
print("="*60 + "\n")
sys.stdout.flush()

