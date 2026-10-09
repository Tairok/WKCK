"""Simplified views for local system monitor - single-computer mode."""

import logging
from datetime import datetime
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from config import Config
from services.sqlite_storage import get_storage
from services.health_prediction_service import AlertService
from services.local_system_service import LocalSystemService
from services.sensor_history import MAX_POINTS, query_series
from services.sensor_service import get_hardware_info, get_hardware_sensors
from services.wmi_service import get_hardware_info as get_wmi_info
from console.spa import spa_shell

logger = logging.getLogger(__name__)


def index(request):
    return spa_shell(request)


@require_http_methods(["GET"])
def health(request):
    """Basic health check."""
    return JsonResponse({"ok": True, "timestamp": datetime.now().isoformat()})


@require_http_methods(["GET"])
def status(request):
    """Get system status - which components are working."""
    try:
        # Get system info
        sys_info = LocalSystemService.get_system_info()
        has_system = "hostname" in sys_info

        # Get hardware info
        hw_info = get_hardware_info()
        has_hardware = len(hw_info) > 0

        # Try to get live sensors
        sensors = get_hardware_sensors()
        has_sensors = len(sensors) > 0

        status_info = {
            "timestamp": datetime.now().isoformat(),
            "running": True,
            "components": {
                "system_info": {"ok": has_system, "message": "System information loaded"},
                "hardware_monitor": {"ok": has_hardware, "message": "LibreHardwareMonitor available"},
                "live_sensors": {"ok": has_sensors, "message": f"Reading live data ({len(sensors)} hardware devices)"},
            }
        }

        return JsonResponse(status_info)
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JsonResponse({
            "timestamp": datetime.now().isoformat(),
            "running": False,
            "error": str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_system_info(request):
    """Get system information."""
    system_info = LocalSystemService.get_system_info()
    return JsonResponse({
        "timestamp": datetime.now().isoformat(),
        "system": system_info,
    })


@require_http_methods(["GET"])
def get_inventory(request):
    """Get system hardware inventory with data from psutil, WMI, and LHM."""
    psutil_inv = LocalSystemService.get_inventory()

    # Transform memory format for frontend
    inventory = {
        "timestamp": datetime.now().isoformat(),
        "system": psutil_inv.get("system", {}),
        "cpu": psutil_inv.get("cpu", {}),
    }

    # Transform memory data: {ram: {total_bytes, used_bytes, ...}} -> {total, used, available, percent}
    memory_data = psutil_inv.get("memory", {})
    if memory_data:
        ram = memory_data.get("ram", {})
        swap = memory_data.get("swap", {})
        inventory["memory"] = {
            "total": ram.get("total_bytes", 0),
            "used": ram.get("used_bytes", 0),
            "available": ram.get("available_bytes", 0),
            "percent": ram.get("percent", 0),
            "swap_total": swap.get("total_bytes", 0),
            "swap_used": swap.get("used_bytes", 0),
        }

    # Transform disk data: {device: {...}} -> [{device, mountpoint, filesystem, total, used, free}]
    disk_data = psutil_inv.get("disks", {})
    inventory["disks"] = []
    if disk_data:
        for device, info in disk_data.items():
            inventory["disks"].append({
                "device": device,
                "mountpoint": info.get("mountpoint", ""),
                "filesystem": info.get("fstype", ""),
                "total": info.get("total_bytes", 0),
                "used": info.get("used_bytes", 0),
                "free": info.get("free_bytes", 0),
            })

    # Add network info
    network_data = psutil_inv.get("network", {})
    if network_data:
        inventory["network"] = network_data

    # Add battery info if available
    battery_data = psutil_inv.get("battery")
    if battery_data:
        inventory["battery"] = battery_data

    # Add WMI hardware info (model, BIOS, motherboard, memory modules, disk details)
    try:
        wmi_info = get_wmi_info()
        if wmi_info:
            inventory["wmi"] = wmi_info
            # Also expose motherboard, bios, system at top level for renderer
            if wmi_info.get("motherboard"):
                inventory["motherboard"] = wmi_info["motherboard"]
            if wmi_info.get("bios"):
                inventory["bios"] = wmi_info["bios"]
            if wmi_info.get("system"):
                inventory["system_hw"] = wmi_info["system"]
    except Exception as e:
        logger.debug(f"[INVENTORY] Failed to get WMI info: {e}")

    # Add LHM hardware devices (detailed hardware list)
    hardware_info = get_hardware_info()
    if hardware_info:
        inventory["hardware_devices"] = hardware_info

    return JsonResponse({
        "timestamp": datetime.now().isoformat(),
        "inventory": inventory,
    })


@require_http_methods(["GET"])
def get_sensor_latest(request):
    """Get current live sensor readings from hardware."""
    sensors = get_hardware_sensors()

    return JsonResponse({
        "timestamp": datetime.now().isoformat(),
        "sensors": sensors,
    })


@require_http_methods(["GET"])
def get_sensor_series(request):
    """Bucketed time series for the chosen sensors over a window (max 24 h)."""
    sensor_ids = request.GET.getlist("sensor")[:20]
    if not sensor_ids:
        return JsonResponse({"error": "At least one sensor parameter is required"}, status=400)

    try:
        window = int(request.GET.get("window", 3600))
    except (TypeError, ValueError):
        window = 3600
    window = max(60, min(window, Config.SENSOR_RETENTION_SECONDS))

    return JsonResponse({
        "timestamp": datetime.now().isoformat(),
        "max_points": MAX_POINTS,
        **query_series(window, sensor_ids),
    })


@require_http_methods(["GET"])
@require_http_methods(["GET"])
def health_analysis(request):
    """Get health analysis/alerts - returns stored alerts from database."""
    storage = get_storage(str(Path(Config.BASE_PATH) / "data" / "sensors.db"))

    # Get latest alerts from database (last hour)
    db_alerts = storage.get_latest_alerts("localhost", hours=1)

    # If no alerts in DB, generate from live sensors and store
    if db_alerts.get("total_alerts", 0) == 0:
        sensors = get_hardware_sensors()
        alerts = AlertService.get_alerts(sensors)

        try:
            storage.store_alerts_batch("localhost", alerts)
            logger.debug(f"[HEALTH] Generated and stored {alerts.get('total_alerts', 0)} live alerts")
        except Exception as e:
            logger.debug(f"[HEALTH] Failed to store alerts: {e}")

    # Return alerts from database (live + recently stored test alerts)
    return JsonResponse({
        "timestamp": db_alerts.get("timestamp", datetime.now().isoformat()),
        "components": db_alerts.get("components", {}),
        "total_alerts": db_alerts.get("total_alerts", 0),
        "critical_count": db_alerts.get("critical_count", 0),
    })


@require_http_methods(["GET"])
def health_summary(request):
    """Get health summary."""
    # Get live sensor data
    sensors = get_hardware_sensors()
    alerts = AlertService.get_alerts(sensors)

    return JsonResponse({
        "timestamp": datetime.now().isoformat(),
        "total_alerts": alerts.get("total_alerts", 0),
        "critical_count": alerts.get("critical_count", 0),
        "components_with_alerts": len(alerts.get("components", {})),
    })


@require_http_methods(["GET"])
def alert_history(request):
    """Get alert history from database."""
    try:
        component = request.GET.get("component")
        level = request.GET.get("level")
        hours = int(request.GET.get("hours", 24))
        limit = int(request.GET.get("limit", 100))
    except (TypeError, ValueError):
        hours = 24
        limit = 100

    storage = get_storage(str(Path(Config.BASE_PATH) / "data" / "sensors.db"))
    history = storage.get_alert_history("localhost", component=component, level=level,
                                       hours=hours, limit=limit)

    return JsonResponse({
        "timestamp": datetime.now().isoformat(),
        "history": history,
    })


@require_http_methods(["GET"])
def debug_alerts(request):
    """Debug endpoint - show what's in database and API response."""
    storage = get_storage(str(Path(Config.BASE_PATH) / "data" / "sensors.db"))

    # Get latest alerts from database
    db_alerts = storage.get_alert_history("localhost", limit=20)

    # Get live alerts from API
    sensors = get_hardware_sensors()
    live_alerts = AlertService.get_alerts(sensors)

    return JsonResponse({
        "timestamp": datetime.now().isoformat(),
        "database": {
            "total_alerts_in_db": len(db_alerts),
            "recent_alerts": db_alerts[:5],
        },
        "live_api": {
            "total_alerts": live_alerts.get("total_alerts", 0),
            "critical_count": live_alerts.get("critical_count", 0),
            "components": live_alerts.get("components", {}),
        },
        "sensors_available": len(sensors) > 0,
    })


