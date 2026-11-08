# BMC Console (mockup)

Panel BMC Console to mockup dashboardu monitoringu komputera. Frontend jest zbudowany w React/Vite, a API dostarcza `json-server` z pliku JSON. Dane, alerty, wykresy i lista kont są przykładowe — aplikacja nie odczytuje sprzętu ani nie używa Django, WMI czy baz SQLite.

## Wymagania

- Node.js 20+
- npm

## Instalacja

W katalogu `frontend/`:

```powershell
npm install
```

## Uruchomienie

Uruchom API i frontend w dwóch terminalach:

```powershell
cd frontend
npm run mock-api
```

```powershell
cd frontend
npm run dev
```

Otwórz http://127.0.0.1:5173. Vite przekazuje żądania `/api` do `json-server` na porcie 8000.

Do sprawdzenia zbudowanej aplikacji:

```powershell
cd frontend
npm run build
npm run preview
```

`npm run preview` także przekazuje `/api` do działającego `json-server`.

## Dane mockupowe

- `frontend/mock-data/db.json` — dane przykładowe do dashboardu; `json-server` zapisuje do tego pliku zmiany, np. dodanych użytkowników.
- `frontend/mock-data/routes.json` — mapowanie dotychczasowych ścieżek `/api/...` na zasoby JSON.
- Główny zestaw danych sprzętowych, sensorów, historii wykresów i alertów można edytować bezpośrednio w `db.json`.

Logowanie jest wyłącznie makietą: wybierz `admin`, `operator` lub `viewer` (albo dodane konto), a hasło nie jest weryfikowane ani zapisywane. Stan sesji jest przechowywany lokalnie w przeglądarce. Nie używaj tej konfiguracji do prawdziwego uwierzytelniania ani w środowisku produkcyjnym.

## Endpointy

| Metoda | Ścieżka | Zasób JSON |
|---|---|---|
| GET | `/api/info` | Informacje o systemie |
| GET | `/api/inventory` | Inwentarz sprzętu |
| GET | `/api/sensors/latest` | Bieżące przykładowe odczyty |
| GET | `/api/sensors/series` | Stałe punkty do wykresów |
| GET | `/api/health/summary` | Podsumowanie alertów |
| GET | `/api/health/analysis` | Alerty komponentów |
| GET | `/api/health/history` | Historia alertów |
| GET, POST | `/api/users` | Lista kont i dodanie konta mockupowego |

Zmiany w `db.json` są zapisywane przez `json-server`. Formularze użytkowników nie wysyłają haseł do API.

## Struktura

```text
frontend/
  mock-data/       Pliki JSON i mapowanie endpointów json-server
  src/api/         Klient API i hooki React Query
  src/auth/        Makietowa sesja logowania przechowywana w przeglądarce
  src/components/  Karty, wskaźnik, szablon wykresu i PageElements.jsx z helperami UI
  src/pages/       Strony i ich właściwe układy/elementy
  src/styles/index.css  Wszystkie style aplikacji i wykresu
  vite.config.js   Konfiguracja developmentu, builda i proxy API
```

Ikony pochodzą z `lucide-react`, a wykresy rysuje biblioteka `uPlot`. Style projektu są utrzymywane w jednym pliku `src/styles/index.css`; `PageElements.jsx` zbiera współdzielone elementy interfejsu, które nie wymagają osobnych komponentów.
