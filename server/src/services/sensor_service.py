"""Hardware sensor service: reads LibreHardwareMonitor data and keeps it polled in the background."""

import logging
import math
import threading
import time
from pathlib import Path
from typing import Dict, Any

from config import Config
from services.sensor_history import record_samples

logger = logging.getLogger(__name__)

_computer = None
_available = False
_lock = threading.Lock()


def initialize(dll_path: str = str(Config.LHM_DLL_PATH)) -> bool:
    """Load LibreHardwareMonitor and open the hardware computer.

    Args:
        dll_path: Path to LibreHardwareMonitorLib.dll

    Returns:
        True if initialization successful
    """
    global _computer, _available

    if _available:
        return True

    try:
        import clr

        dll_full_path = Path(dll_path).absolute()
        if not dll_full_path.exists():
            logger.error(f"[SENSORS] DLL not found: {dll_full_path}")
            return False

        clr.AddReference(str(dll_full_path))

        from LibreHardwareMonitor.Hardware import Computer

        _computer = Computer()
        _computer.IsCpuEnabled = True
        _computer.IsGpuEnabled = True
        _computer.IsMemoryEnabled = True
        _computer.IsMotherboardEnabled = True
        _computer.IsControllerEnabled = True
        _computer.IsNetworkEnabled = True
        _computer.IsStorageEnabled = True

        _computer.Open()
        _available = True

        logger.info("[SENSORS] LibreHardwareMonitor initialized")
        return True

    except ImportError as e:
        logger.error(f"[SENSORS] pythonnet not available: {e}")
        return False
    except Exception as e:
        logger.error(f"[SENSORS] Failed to initialize: {e}")
        return False


def _collect_sensors(hardware, hw_sensors: Dict[str, Any]) -> None:
    """Add readable sensors of one hardware item into hw_sensors."""
    update_hardware(hardware)

    for sensor in hardware.Sensors:
        sensor_type = str(sensor.SensorType)
        sensor_name = sensor.Name or "Unknown"
        full_name = f"{sensor_type}: {sensor_name}"
        # NaN/inf are not valid JSON and become NULL in SQLite, so treat them as "no reading"
        value = float(sensor.Value) if sensor.Value is not None else None
        if value is not None and not math.isfinite(value):
            value = None

        if value is not None:
            hw_sensors[full_name] = {
                "current": value,
                "min": getattr(sensor, 'Min', None),
                "max": getattr(sensor, 'Max', None),
            }


def get_hardware_sensors() -> Dict[str, Any]:
    """Get all hardware sensors.

    Returns:
        Dict with hardware sensors grouped by hardware name
        Format: {hardware_name: {sensor_name: {current, min, max}}}
    """
    if not _available or _computer is None:
        return {}

    try:
        sensors = {}

        for hardware in _computer.Hardware:
            hw_sensors = {}
            _collect_sensors(hardware, hw_sensors)

            for sub_hardware in hardware.SubHardware:
                _collect_sensors(sub_hardware, hw_sensors)

            if hw_sensors:
                sensors[hardware.Name] = hw_sensors

        logger.debug(f"[SENSORS] Collected sensors from {len(sensors)} hardware devices")
        return sensors

    except Exception as e:
        logger.error(f"[SENSORS] Failed to read sensors: {e}")
        return {}


def get_hardware_info() -> Dict[str, Any]:
    """Get hardware inventory.

    Returns:
        Dict with hardware information grouped by hardware type
    """
    if not _available or _computer is None:
        return {}

    try:
        hardware_info = {}

        for hardware in _computer.Hardware:
            hw_data = {
                "name": hardware.Name,
                "type": str(hardware.HardwareType) if hardware.HardwareType else "Unknown",
                "sub_hardware": []
            }

            for sub_hw in hardware.SubHardware:
                hw_data["sub_hardware"].append({
                    "name": sub_hw.Name,
                    "type": str(sub_hw.HardwareType) if sub_hw.HardwareType else "Unknown"
                })

            hw_id = str(hardware.HardwareType) if hardware.HardwareType else "Other"
            hardware_info.setdefault(hw_id, []).append(hw_data)

        logger.debug(f"[SENSORS] Found {len(hardware_info)} hardware types")
        return hardware_info

    except Exception as e:
        logger.error(f"[SENSORS] Failed to read hardware info: {e}")
        return {}


def update_hardware(hardware) -> None:
    """Refresh readings of one hardware item (errors are logged, not raised)."""
    try:
        hardware.Update()
    except Exception as e:
        logger.debug(f"[SENSORS] Failed to update hardware: {e}")


class SensorService:
    """Owns the LibreHardwareMonitor session and a background polling thread."""

    _running = False
    _thread = None

    @staticmethod
    def start() -> bool:
        """Initialize LibreHardwareMonitor and start the polling thread (idempotent)."""
        with _lock:
            if SensorService._running:
                return True

            if not initialize():
                logger.warning("[SENSORS] LibreHardwareMonitor unavailable, continuing with psutil only")

            SensorService._running = True
            SensorService._thread = threading.Thread(
                target=SensorService._poll_loop,
                daemon=True,
                name="SensorPoller"
            )
            SensorService._thread.start()
            logger.info("[SENSORS] Polling started (interval=%ds)", Config.LHM_POLL_INTERVAL_SECONDS)
            return True

    @staticmethod
    def stop() -> None:
        """Stop polling and close LibreHardwareMonitor."""
        global _computer, _available

        with _lock:
            SensorService._running = False
            if SensorService._thread:
                SensorService._thread.join(timeout=2)
                SensorService._thread = None

            try:
                if _computer is not None:
                    _computer.Close()
            except Exception as e:
                logger.error(f"[SENSORS] Failed to close: {e}")
            finally:
                _computer = None
                _available = False
            logger.info("[SENSORS] Polling stopped")

    @staticmethod
    def _poll_loop() -> None:
        """Refresh sensor readings periodically so API calls return fresh data."""
        while SensorService._running:
            try:
                record_samples(get_hardware_sensors())
            except Exception as e:
                logger.debug("[SENSORS] Poll error: %s", e)

            time.sleep(Config.LHM_POLL_INTERVAL_SECONDS)
