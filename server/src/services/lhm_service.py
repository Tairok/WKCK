"""Service for reading hardware data directly from LibreHardwareMonitor library."""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

_computer = None
_lhm_available = False


def initialize_lhm(dll_path: str) -> bool:
    """Initialize LibreHardwareMonitor library.

    Args:
        dll_path: Path to LibreHardwareMonitorLib.dll

    Returns:
        True if initialization successful
    """
    global _computer, _lhm_available

    if _lhm_available:
        return True

    try:
        import clr

        dll_full_path = Path(dll_path).absolute()
        if not dll_full_path.exists():
            logger.error(f"[LHM] DLL not found: {dll_full_path}")
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
        _lhm_available = True

        logger.info("[LHM] Library initialized successfully")
        return True

    except ImportError as e:
        logger.error(f"[LHM] pythonnet not available: {e}")
        return False
    except Exception as e:
        logger.error(f"[LHM] Failed to initialize: {e}")
        return False


def get_hardware_sensors() -> Dict[str, Any]:
    """Get all hardware sensors from LibreHardwareMonitor.

    Returns:
        Dict with hardware sensors grouped by type
        Format: {hardware_name: {sensor_name: {current, min, max}}}
    """
    if not _lhm_available or _computer is None:
        return {}

    try:
        sensors = {}

        for hardware in _computer.Hardware:
            hw_name = hardware.Name
            hw_sensors = {}

            update_hardware(hardware)

            for sensor in hardware.Sensors:
                sensor_type = str(sensor.SensorType)
                sensor_name = sensor.Name or "Unknown"
                full_name = f"{sensor_type}: {sensor_name}"
                value = float(sensor.Value) if sensor.Value is not None else None

                if value is not None:
                    hw_sensors[full_name] = {
                        "current": value,
                        "min": getattr(sensor, 'Min', None),
                        "max": getattr(sensor, 'Max', None),
                    }

            for sub_hardware in hardware.SubHardware:
                update_hardware(sub_hardware)

                for sensor in sub_hardware.Sensors:
                    sensor_type = str(sensor.SensorType)
                    sensor_name = sensor.Name or "Unknown"
                    full_name = f"{sensor_type}: {sensor_name}"
                    value = float(sensor.Value) if sensor.Value is not None else None

                    if value is not None:
                        hw_sensors[full_name] = {
                            "current": value,
                            "min": getattr(sensor, 'Min', None),
                            "max": getattr(sensor, 'Max', None),
                        }

            if hw_sensors:
                sensors[hw_name] = hw_sensors

        logger.debug(f"[LHM] Collected sensors from {len(sensors)} hardware devices")
        return sensors

    except Exception as e:
        logger.error(f"[LHM] Failed to read sensors: {e}")
        return {}


def get_hardware_info() -> Dict[str, Any]:
    """Get hardware inventory from LibreHardwareMonitor.

    Returns:
        Dict with hardware information
    """
    if not _lhm_available or _computer is None:
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
            if hw_id not in hardware_info:
                hardware_info[hw_id] = []

            hardware_info[hw_id].append(hw_data)

        logger.debug(f"[LHM] Found {len(hardware_info)} hardware types")
        return hardware_info

    except Exception as e:
        logger.error(f"[LHM] Failed to read hardware info: {e}")
        return {}


def update_hardware(hardware) -> None:
    """Update hardware sensor readings.

    Args:
        hardware: Hardware object from LibreHardwareMonitor
    """
    try:
        hardware.Update()
    except Exception as e:
        logger.debug(f"[LHM] Failed to update hardware: {e}")


def shutdown_lhm() -> None:
    """Shutdown LibreHardwareMonitor."""
    global _computer, _lhm_available

    try:
        if _computer is not None:
            _computer.Close()
            _computer = None
            _lhm_available = False
            logger.info("[LHM] Library shutdown")
    except Exception as e:
        logger.error(f"[LHM] Failed to shutdown: {e}")
