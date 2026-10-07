import platform
from pathlib import Path


class Config:
    """Configuration for Local System Monitor - reads hardware data from localhost."""

    OS = platform.system()

    # Runtime server configuration
    TCP_IP_HOST = "127.0.0.1"
    SERVER_PORT = 8000
    TIMEZONE = "Europe/Warsaw"

    # Security
    SECRET_KEY = "bmc-dev-secret-local-monitor"

    # Allowed hosts for Django
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

    # Paths
    BASE_PATH = Path(__file__).parent
    DATA_PATH = BASE_PATH / "data"
    LOG_PATH = BASE_PATH / "logs" / "logs.log"

    # Logging
    LOG_CONSOLE_LEVEL = "WARNING"
    LOG_FILE_LEVEL = "DEBUG"

    # OpenHardwareMonitor polling (local)
    OHM_PORT = 8085
    OHM_POLL_INTERVAL_SECONDS = 2
    OHM_HTTP_TIMEOUT_SECONDS = 3

    @staticmethod
    def get_base_path():
        return Config.BASE_PATH
