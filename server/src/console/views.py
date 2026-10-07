"""Simplified views for local system monitor."""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from services.sensor_data_service import get_collector
from services.health_prediction_service import AlertService
from services.local_system_service import LocalSystemService
from services.ohm_poller_service import LOCAL_AGENT_ID

logger = logging.getLogger(__name__)


def index(request):
    """Serve the main dashboard page."""
    return render(request, "index.html")


def health(request):
    """Basic health check."""
    return JsonResponse({"ok": True, "timestamp": datetime.now().isoformat()})


@require_http_methods(["GET"])
def health_analysis(request, agent_id=None):
    """Get health analysis/alerts for sensors."""
    agent_id = agent_id or LOCAL_AGENT_ID
    collector = get_collector()

    # Get latest sensor data
    latest = collector.get_latest(agent_id)

    # Generate alerts based on sensor data
    alerts = AlertService.get_alerts(latest)

    return JsonResponse({
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "alerts": alerts,
    })


@require_http_methods(["GET"])
def health_summary(request, agent_id=None):
    """Get health summary."""
    agent_id = agent_id or LOCAL_AGENT_ID
    collector = get_collector()

    latest = collector.get_latest(agent_id)
    alerts = AlertService.get_alerts(latest)

    return JsonResponse({
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "total_alerts": alerts.get("total_alerts", 0),
        "critical_count": alerts.get("critical_count", 0),
        "components_with_alerts": len(alerts.get("components", {})),
    })


@require_http_methods(["GET"])
def agents(request):
    """List available agents (just localhost for local monitor)."""
    system_info = LocalSystemService.get_system_info()

    return JsonResponse({
        "agents": [
            {
                "agent_id": LOCAL_AGENT_ID,
                "hostname": system_info.get("hostname", "localhost"),
                "status": "active",
                "is_local": True,
            }
        ]
    })


@require_http_methods(["GET"])
def agent_inventory(request, agent_id):
    """Get system hardware inventory."""
    if agent_id != LOCAL_AGENT_ID:
        return JsonResponse({"error": "Only localhost is available"}, status=404)

    inventory = LocalSystemService.get_inventory()

    return JsonResponse({
        "agent_id": agent_id,
        "inventory": inventory,
    })


@require_http_methods(["GET"])
def get_sensor_latest(request, agent_id):
    """Get latest sensor readings."""
    if agent_id != LOCAL_AGENT_ID:
        return JsonResponse({"error": "Only localhost is available"}, status=404)

    collector = get_collector()
    latest = collector.get_latest(agent_id)

    return JsonResponse({
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "sensors": latest,
    })


@require_http_methods(["GET"])
def get_sensor_history(request, agent_id):
    """Get sensor history with optional limit."""
    if agent_id != LOCAL_AGENT_ID:
        return JsonResponse({"error": "Only localhost is available"}, status=404)

    try:
        limit = int(request.GET.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100

    collector = get_collector()
    history = collector.get_history(agent_id, limit=limit)

    return JsonResponse({
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "history": history,
    })


@require_http_methods(["GET"])
def get_sensor_stats(request, agent_id):
    """Get sensor statistics."""
    if agent_id != LOCAL_AGENT_ID:
        return JsonResponse({"error": "Only localhost is available"}, status=404)

    group_name = request.GET.get("group")
    sensor_name = request.GET.get("sensor")

    if not group_name or not sensor_name:
        return JsonResponse({
            "error": "group and sensor query parameters are required"
        }, status=400)

    collector = get_collector()
    stats = collector.get_stats(agent_id, group_name, sensor_name)

    return JsonResponse({
        "agent_id": agent_id,
        "group": group_name,
        "sensor": sensor_name,
        "stats": stats,
    })
