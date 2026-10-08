from django.urls import path
from console import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/health", views.health, name="api_health"),
    path("api/status", views.status, name="api_status"),
    path("api/info", views.get_system_info, name="api_info"),
    path("api/inventory", views.get_inventory, name="api_inventory"),
    path("api/sensors/latest", views.get_sensor_latest, name="api_sensor_latest"),
    path("api/sensors/history", views.get_sensor_history, name="api_sensor_history"),
    path("api/sensors/stats", views.get_sensor_stats, name="api_sensor_stats"),
    path("api/health/analysis", views.health_analysis, name="api_health_analysis"),
    path("api/health/summary", views.health_summary, name="api_health_summary"),
    path("api/health/history", views.alert_history, name="api_alert_history"),
    path("api/health/debug", views.debug_alerts, name="api_debug_alerts"),
    path("api/agents/<str:agent_id>/health/analysis", views.agent_health_analysis, name="api_agent_health_analysis"),
]
