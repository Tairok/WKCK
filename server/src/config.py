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

    # LibreHardwareMonitor integration
    LHM_DLL_PATH = BASE_PATH.parent.parent / "resources" / "LibreHardwareMonitor" / "LibreHardwareMonitorLib.dll"
    LHM_POLL_INTERVAL_SECONDS = 2

    @staticmethod
    def get_base_path():
        return Config.BASE_PATH
