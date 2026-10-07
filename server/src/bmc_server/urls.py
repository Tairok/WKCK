from django.urls import path
from console import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/health", views.health, name="api_health"),
    path("api/health/analysis", views.health_analysis, name="api_health_analysis"),
    path("api/health/summary", views.health_summary, name="api_health_summary"),
    path("api/agents", views.agents, name="api_agents"),
    path("api/agents/<str:agent_id>/inventory", views.agent_inventory, name="api_agent_inventory"),
    path("api/agents/<str:agent_id>/sensors/latest", views.get_sensor_latest, name="api_sensor_latest"),
    path("api/agents/<str:agent_id>/sensors/history", views.get_sensor_history, name="api_sensor_history"),
    path("api/agents/<str:agent_id>/sensors/stats", views.get_sensor_stats, name="api_sensor_stats"),
]
