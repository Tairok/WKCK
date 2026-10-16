# BMC Console (Local System Monitor)

Local web dashboard for the Windows machine it runs on: hardware inventory, live sensor readings,
1-hour and 24-hour sensor charts, threshold health alerts, and login protected by TOTP (MFA).

Installation guide in Polish: `resources/instrukcja`.

## Requirements

- Windows 10/11 (inventory and sensors use WMI and LibreHardwareMonitor)
- Python 3.12
- Node.js 20+ (only to build the frontend)
- LibreHardwareMonitor DLL in `resources/LibreHardwareMonitor/`

## Setup

In an Administrator PowerShell, from the repository root:

```powershell
.\install.ps1
```

It creates the virtual environment, installs the Python packages, builds the frontend and creates the runtime folders. LibreHardwareMonitor does not need to run in the background: the server loads its DLL directly.

## Run

```powershell
cd server\src
..\..\.venv\Scripts\python.exe -m daphne -b 127.0.0.1 -p 8000 bmc_server.asgi:application
```

Sensor readings require the server to run as Administrator. The application log is in `server/src/logs/logs.log`.

Open http://127.0.0.1:8000. The first visit creates the administrator account and shows a QR code for the authenticator app.

Development with hot reload: run daphne as above, then `npm run dev` in `frontend/` (port 5173, `/api` is proxied to 8000).

## Configuration

Main settings live in `server/src/config.py`:

- `TCP_IP_HOST`, `SERVER_PORT`, `ALLOWED_HOSTS`
- `TIMEZONE`
- `SECRET_KEY`
- `LHM_POLL_INTERVAL_SECONDS` (sensor sampling, 1 s)
- `SENSOR_RETENTION_SECONDS` (chart history, 24 h)

Environment variables:

- `BMC_DJANGO_DEBUG` (default `1`; set to `0` outside development)
- `BMC_LOG_CONSOLE_LEVEL`, `BMC_LOG_FILE_LEVEL`

## Data and logs

Runtime files are created under `server/src/data/` and `server/src/logs/`:

- `users.db` - user accounts and sessions
- `sensors.db` - stored health alerts
- `sensor_history.db` - sensor samples for charts (rolling 24 h)
- `logs/logs.log` - application log

These files are excluded from git.

## API

All endpoints except `/api/health`, `/api/status` and `/api/auth/*` require a session.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/info` | Host, OS and uptime |
| GET | `/api/inventory` | CPU, memory, disks, network, optional hardware sections |
| GET | `/api/sensors/latest` | Current sensor readings |
| GET | `/api/sensors/series?window=&sensor=` | Chart data (window up to 86400 s, up to 20 sensors) |
| GET | `/api/health/summary` | Alert counters |
| GET | `/api/health/analysis` | Current alerts per component |
| GET | `/api/health/history` | Stored alert history |
| POST | `/api/auth/login`, `/api/auth/register`, `/api/auth/mfa/verify`, `/api/auth/logout` | Authentication |

## Tests

```powershell
cd server\src
python -m unittest discover -s tests -t .
```

## Structure

```
server/src/
  bmc_server/        Django project: settings, urls, asgi
  console/           Views, auth views and middleware, SPA shell
  services/          Sensors, system info, health alerts, user storage, sensor history
  frontend_dist/     Built frontend (generated, not in git)
  tests/             Unit tests
frontend/            React + Vite source (Tailwind, react-query, uPlot)
resources/           LibreHardwareMonitor library and installation guide
```

## Before handover

- Change `SECRET_KEY` in `config.py` and run with `BMC_DJANGO_DEBUG=0`.
- Create the administrator account on the target machine; do not ship `users.db`.
