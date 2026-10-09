from django.urls import path, re_path
from console import views, auth_views
from console.spa import spa_shell

urlpatterns = [
    path("", views.index, name="index"),
    path("auth/login", auth_views.auth_page, name="auth_login"),
    path("auth/register", auth_views.auth_page, name="auth_page"),
    path("api/health", views.health, name="api_health"),
    path("api/status", views.status, name="api_status"),
    path("api/info", views.get_system_info, name="api_info"),
    path("api/inventory", views.get_inventory, name="api_inventory"),
    path("api/sensors/latest", views.get_sensor_latest, name="api_sensor_latest"),
    path("api/sensors/series", views.get_sensor_series, name="api_sensor_series"),
    path("api/health/analysis", views.health_analysis, name="api_health_analysis"),
    path("api/health/summary", views.health_summary, name="api_health_summary"),
    path("api/health/history", views.alert_history, name="api_alert_history"),
    path("api/health/debug", views.debug_alerts, name="api_debug_alerts"),
    path("api/auth/register", auth_views.register, name="api_auth_register"),
    path("api/auth/login", auth_views.login, name="api_auth_login"),
    path("api/auth/logout", auth_views.logout, name="api_auth_logout"),
    path("api/auth/me", auth_views.me, name="api_auth_me"),
    path("api/auth/status", auth_views.status, name="api_auth_status"),
    path("api/auth/mfa/verify", auth_views.mfa_verify, name="api_auth_mfa_verify"),
    re_path(r"^(?!api/|static/|assets/).*$", spa_shell, name="spa"),
]
