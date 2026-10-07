#!/usr/bin/env python
"""
Start the BMC server with Daphne ASGI server (required for WebSockets)
"""

import os
import sys
import signal
import logging
from pathlib import Path

import django
from daphne.cli import CommandLineInterface

# --- Django settings ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmc_server.settings")

# --- Add src to PYTHONPATH ---
src_dir = Path(__file__).parent / "server" / "src"
sys.path.insert(0, str(src_dir))

# --- Setup Django ---
django.setup()

# --- Logging ---
logger = logging.getLogger(__name__)
logger.info("Server starting — client logs cleared")

# --- Services ---
from server.src.services.client_logs_service import ClientLogsService
from server.src.services.data_initializer import DataInitializer
from server.src.services.ohm_poller_service import OHMPollerService

# --- Clear logs ---
ClientLogsService.clear_all_logs()

# --- Initialize MariaDB ---
try:
    DataInitializer.initialize()
    logger.info("[INIT] MariaDB initialized successfully")
except Exception as e:
    logger.error(f"[INIT] MariaDB initialization failed: {e}")

# --- Start OHM polling service ---
try:
    OHMPollerService.start()
    logger.info("[INIT] OHM Poller service started")
except Exception as e:
    logger.warning(f"[INIT] OHM Poller initialization failed: {e}")


# --- Shutdown handlers ---
def cleanup_on_shutdown():
    logger.info("Server shutting down...")
    raise SystemExit(0)


def handle_shutdown(signum, frame):
    cleanup_on_shutdown()


# --- Daphne startup ---
if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    sys.argv = [
        "daphne",
        "-b", "0.0.0.0",
        "-p", "8000",
        "bmc_server.asgi:application",
    ]

    try:
        CommandLineInterface().run(sys.argv[1:])
    except KeyboardInterrupt:
        cleanup_on_shutdown()
