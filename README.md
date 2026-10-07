# Local System Monitor

A simplified Django web application that reads hardware and system information from the local computer.

## Features

- **System Information**: Hostname, OS, architecture, uptime
- **Hardware Inventory**: CPU, RAM, disk drives, network interfaces, battery status
- **Sensor Monitoring**: CPU/memory/disk usage, temperatures, fan speeds (if available)
- **Health Alerts**: Real-time alerts based on sensor thresholds
- **Web Dashboard**: Overview, Inventory, Sensors, and Health tabs
- **REST API**: JSON endpoints for all data

## Installation & Startup

### 1. Setup Virtual Environment

```bash
cd BMC_server
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run as ASGI

**Option A: Daphne (Production)**
```bash
cd server/src
daphne -b 0.0.0.0 -p 8000 bmc_server.asgi:application
```

**Option B: Django Development Server**
```bash
cd server/src
python manage.py runserver 0.0.0.0:8000
```

Server starts on: `http://127.0.0.1:8000`

## Configuration

Edit `server/src/config.py` to customize:

- `TCP_IP_HOST` - Server bind address (default: 127.0.0.1)
- `SERVER_PORT` - Server port (default: 8000)
- `TIMEZONE` - Timezone for timestamps (default: Europe/Warsaw)
- `OHM_PORT` - OpenHardwareMonitor API port (default: 8085)
- `OHM_POLL_INTERVAL_SECONDS` - Polling interval (default: 2)

## Optional: OpenHardwareMonitor Integration

To add hardware sensor data from OpenHardwareMonitor:

1. Install OpenHardwareMonitor on Windows
2. Run OpenHardwareMonitor with web server enabled
3. Configure `OHM_PORT` in config.py (default: 8085)

The monitor will automatically combine psutil data with OHM data if available.

## API Endpoints

All endpoints accept only localhost as the agent ID.

- `GET /` - Dashboard
- `GET /api/health` - Health check
- `GET /api/health/analysis` - Detailed alerts and analysis
- `GET /api/health/summary` - Alert summary
- `GET /api/agents` - List available agents (localhost)
- `GET /api/agents/localhost/inventory` - Hardware inventory
- `GET /api/agents/localhost/sensors/latest` - Latest sensor readings
- `GET /api/agents/localhost/sensors/history?limit=100` - Sensor history
- `GET /api/agents/localhost/sensors/stats?group=...&sensor=...` - Sensor statistics

## Development

### Django Management Commands

Run from `server/src` directory:

```bash
cd server/src

# Verify configuration
python manage.py check

# Collect static files
python manage.py collectstatic --noinput

# Django interactive shell
python manage.py shell

# Create logs directory
mkdir logs  # Windows: md logs
```

### View Logs

```bash
# Windows
Get-Content -Path server/src/logs/logs.log -Tail 50 -Wait

# Linux/macOS
tail -f server/src/logs/logs.log
```

## Architecture

- **Frontend**: HTML/CSS/JavaScript dashboard (no framework)
- **Backend**: Django + Daphne ASGI
- **Data Collection**: psutil (system) + OpenHardwareMonitor API (optional sensors)
- **Storage**: In-memory sensor history (configurable max entries)

## Simplified from Original

This is a simplified version of the original BMC Server. Removed:

- Remote agent management and registration
- KVM/VNC viewer and remote control
- Database (MariaDB/PostgreSQL)
- User authentication and login
- Lifecycle and server logging
- Command queuing system
- UART and HID device control
- ACPI power commands
