"""Service for keeping LibreHardwareMonitor data fresh for live API access."""

import logging
import threading
import time
from config import Config
from services.lhm_service import initialize_lhm, get_hardware_sensors, shutdown_lhm

logger = logging.getLogger(__name__)

LOCAL_AGENT_ID = "localhost"


class OHMPollerService:
    """Polls LibreHardwareMonitor library and collects hardware/sensor data."""

    _running = False
    _thread = None
    _lock = threading.Lock()

    @staticmethod
    def start():
        """Start hardware sensor polling daemon thread if not already running."""
        with OHMPollerService._lock:
            if OHMPollerService._running:
                return True

            if not initialize_lhm(str(Config.LHM_DLL_PATH)):
                logger.warning("[HARDWARE_POLLER] LibreHardwareMonitor initialization failed, continuing with psutil only")

            OHMPollerService._running = True
            OHMPollerService._thread = threading.Thread(
                target=OHMPollerService._poll_loop,
                daemon=True,
                name="HardwarePoller"
            )
            OHMPollerService._thread.start()
            logger.info("[HARDWARE_POLLER] Service started (interval=%ds)", Config.LHM_POLL_INTERVAL_SECONDS)
            return True

    @staticmethod
    def stop():
        """Stop hardware sensor polling thread."""
        with OHMPollerService._lock:
            OHMPollerService._running = False
            if OHMPollerService._thread:
                OHMPollerService._thread.join(timeout=2)
                OHMPollerService._thread = None
            shutdown_lhm()
            logger.info("[HARDWARE_POLLER] Service stopped")

    @staticmethod
    def _poll_loop():
        """Main polling loop: keep LibreHardwareMonitor updated with fresh data."""
        while OHMPollerService._running:
            try:
                # Just refresh the hardware data by calling get_hardware_sensors
                # This keeps the data fresh and ready for live API calls
                sensors = get_hardware_sensors()
                if sensors:
                    logger.debug("[HARDWARE_POLLER] Refreshed %d hardware devices", len(sensors))

            except Exception as e:
                logger.debug("[HARDWARE_POLLER] Poll error: %s", e)

            time.sleep(Config.LHM_POLL_INTERVAL_SECONDS)
