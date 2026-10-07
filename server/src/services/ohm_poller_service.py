"""Service for polling OpenHardwareMonitor data from local host and collecting sensor data."""

import logging
import threading
import time
import requests
from config import Config
from services.sensor_data_service import get_collector
from services.local_system_service import LocalSystemService

logger = logging.getLogger(__name__)

LOCAL_AGENT_ID = "localhost"


class OHMPollerService:
    """Polls OpenHardwareMonitor REST API on localhost and collects sensor data."""

    _running = False
    _thread = None
    _lock = threading.Lock()

    @staticmethod
    def start():
        """Start OHM polling daemon thread if not already running."""
        with OHMPollerService._lock:
            if OHMPollerService._running:
                return True

            OHMPollerService._running = True
            OHMPollerService._thread = threading.Thread(
                target=OHMPollerService._poll_loop,
                daemon=True,
                name="OHMPoller"
            )
            OHMPollerService._thread.start()
            logger.info("[OHM_POLLER] Service started (interval=%ds, timeout=%ds, port=%d)",
                       Config.OHM_POLL_INTERVAL_SECONDS,
                       Config.OHM_HTTP_TIMEOUT_SECONDS,
                       Config.OHM_PORT)
            return True

    @staticmethod
    def stop():
        """Stop OHM polling thread."""
        with OHMPollerService._lock:
            OHMPollerService._running = False
            if OHMPollerService._thread:
                OHMPollerService._thread.join(timeout=2)
                OHMPollerService._thread = None
            logger.info("[OHM_POLLER] Service stopped")

    @staticmethod
    def _poll_loop():
        """Main polling loop: fetch OHM data and local system data, collect sensors."""
        while OHMPollerService._running:
            try:
                # Get local system sensor data
                local_sensors = LocalSystemService.get_sensor_data()

                # Try to fetch additional data from local OHM if available
                ohm_sensors = fetch_ohm_sensors("127.0.0.1", Config.OHM_PORT, Config.OHM_HTTP_TIMEOUT_SECONDS)

                # Merge sensor data (OHM overrides/extends local data)
                if ohm_sensors:
                    local_sensors.update(ohm_sensors)

                # Update collector with merged sensor data
                if local_sensors:
                    collector = get_collector()
                    collector.collect(LOCAL_AGENT_ID, local_sensors)
                    logger.debug("[OHM_POLLER] Updated %d sensor groups", len(local_sensors))

            except Exception as e:
                logger.debug("[OHM_POLLER] Poll error: %s", e)

            time.sleep(Config.OHM_POLL_INTERVAL_SECONDS)


def fetch_ohm_sensors(host_ip: str, port: int, timeout: int) -> dict:
    """
    Fetch sensor data from OpenHardwareMonitor Remote Web Server and parse into
    sensor dict format compatible with flatten_sensors_for_timescaledb.

    Returns: {hardware_name: {sensor_key: {current, min, max}}} or {} on error
    """
    url = f"http://{host_ip}:{port}/data.json"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        root = response.json()
    except Exception as e:
        logger.debug("[OHM_FETCH] Failed to fetch %s: %s", url, e)
        return {}

    if not isinstance(root, dict):
        return {}

    sensors = {}
    children = root.get("Children", [])

    for hardware in children:
        if not isinstance(hardware, dict):
            continue

        hw_name = hardware.get("Text", "Hardware")
        hw_sensors = {}
        hw_children = hardware.get("Children", [])

        for category_node in hw_children:
            if not isinstance(category_node, dict):
                continue

            category_name = category_node.get("Text", "Unknown")
            sensor_nodes = category_node.get("Children", [])

            for sensor_node in sensor_nodes:
                if not isinstance(sensor_node, dict):
                    continue

                sensor_text = sensor_node.get("Text", "")
                value_str = sensor_node.get("Value", "-")
                min_str = sensor_node.get("Min", "-")
                max_str = sensor_node.get("Max", "-")

                value = _parse_number(value_str)
                if value is None:
                    continue

                sensor_key = f"{category_name}: {sensor_text}"
                hw_sensors[sensor_key] = {
                    "current": value,
                    "min": _parse_number(min_str),
                    "max": _parse_number(max_str),
                }

        if hw_sensors:
            sensors[hw_name] = hw_sensors

    return sensors


def _parse_number(value_str: str) -> float:
    """Extract numeric value from string (handles units like '45.0 °C', '1234 RPM', etc.)."""
    if not value_str or value_str == "-":
        return None

    value_str = value_str.strip()

    chars = []
    for ch in value_str:
        if ch in '-0123456789.,':
            chars.append(ch)
        elif ch.isspace() or ch in '°%RPMCFVWAbps':
            continue
        else:
            break

    if not chars:
        return None

    num_str = ''.join(chars).replace(',', '').replace(' ', '')

    try:
        return float(num_str)
    except ValueError:
        return None
