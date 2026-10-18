# BMC Console (Monitor lokalnego systemu)

## Wymagania

- Windows 10/11 
- Python 3.12
- Node.js 20+ (potrzebny tylko do zbudowania frontendu)
- Biblioteka LibreHardwareMonitor w `resources/LibreHardwareMonitor/`

## Instalacja

W katalogu głównym projektu:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

cd frontend
npm install
npm run build
cd ..
```

Polecenie `npm run build` zapisuje zbudowany frontend w `server/src/frontend_dist/`.

## Uruchomienie

Uruchom PowerShell jako administrator:

```powershell
cd server\src
..\..\.venv\Scripts\python.exe -m daphne -b 127.0.0.1 -p 8000 bmc_server.asgi:application
```

Odczyty czujników wymagają uruchomienia serwera jako administrator. LibreHardwareMonitor nie musi działać w tle, ponieważ serwer ładuje jego bibliotekę DLL bezpośrednio. Log aplikacji znajduje się w `server/src/logs/logs.log`.

Otwórz http://127.0.0.1:8000. Przy pierwszej wizycie tworzysz konto administratora i skanujesz kod QR w aplikacji uwierzytelniającej.

Tryb deweloperski: ustaw `BMC_DJANGO_DEBUG=1`, uruchom daphne jak wyżej, a następnie w katalogu `frontend/` wykonaj `npm run dev` (port 5173; zapytania `/api` są przekazywane na port 8000).

Jeśli frontend nie został zbudowany, serwer zwraca kod HTTP 503 z informacją o konieczności wykonania `npm run build`.

## Konfiguracja

Główne ustawienia znajdują się w `server/src/config.py`:

- `TCP_IP_HOST`, `SERVER_PORT`, `ALLOWED_HOSTS`
- `TIMEZONE`
- `LHM_POLL_INTERVAL_SECONDS` (częstotliwość próbkowania czujników, 1 s)
- `SENSOR_RETENTION_SECONDS` (czas przechowywania historii wykresów, 24 h)

Zmienne środowiskowe:

- `BMC_SECRET_KEY` - klucz Django. Jeśli nie jest ustawiony, przy każdym starcie generowany jest losowy klucz.
- `BMC_DJANGO_DEBUG` - tryb debugowania, domyślnie `0`. Ustaw `1` podczas developmentu.
- `BMC_LOG_CONSOLE_LEVEL`, `BMC_LOG_FILE_LEVEL` - poziomy logowania.

## Dane i logi

Pliki tworzone są w katalogach `server/src/data/` i `server/src/logs/`:

- `users.db` - konta użytkowników i sesje
- `sensors.db` - zapisane alerty zdrowia
- `sensor_history.db` - próbki czujników do wykresów (przechowywane 24 h)
- `logs/logs.log` - log aplikacji


## API

Wszystkie endpointy oprócz  `/api/auth/*` wymagają aktywnej sesji.

| Metoda | Ścieżka | Opis |
|---|---|---|
| GET | `/api/info` | Nazwa hosta, system i czas działania |
| GET | `/api/inventory` | Procesor, pamięć, dyski, sieć oraz opcjonalne sekcje sprzętowe |
| GET | `/api/sensors/latest` | Bieżące odczyty czujników |
| GET | `/api/sensors/series?window=&sensor=` | Dane do wykresów (okno do 86400 s, do 20 czujników) |
| GET | `/api/health/summary` | Liczniki alertów |
| GET | `/api/health/analysis` | Bieżące alerty dla każdego komponentu |
| GET | `/api/health/history` | Historia zapisanych alertów |
| GET, POST | `/api/users` | Lista kont i dodawanie nowego konta |
| POST | `/api/auth/login`, `/api/auth/register`, `/api/auth/mfa/verify`, `/api/auth/logout` | Uwierzytelnianie |

## Testy

```powershell
cd server\src
python -m unittest discover -s tests -t .
```

## Struktura

```
server/src/
  bmc_server/        Projekt Django: ustawienia, adresy URL, asgi
  console/           Widoki, widoki uwierzytelniania i middleware, powłoka SPA
  services/          Czujniki, informacje o systemie, alerty, WMI, baza użytkowników, historia czujników
  frontend_dist/     Zbudowany frontend (generowany, nie jest w git)
  tests/             Testy 
frontend/            Kod źródłowy React + Vite (Tailwind, react-query, uPlot)
resources/           Biblioteka LibreHardwareMonitor i instrukcja instalacji
```
