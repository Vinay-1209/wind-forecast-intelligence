# Wind Forecast Intelligence

Decision-time UK national wind forecasts compared with actual generation for day-ahead procurement decisions in January 2026.

The app shows the forecast a buyer could see at or before the **09:50 Europe/London** cutoff on the day before delivery, then measures how far that forecast was from Elexon outturn. It does not invent prices, savings, or look-ahead forecasts.

Data source: [Elexon Insights API](https://data.elexon.co.uk/bmrs/api/v1) — `FUELHH` (fuelType=WIND) and `WINDFOR` streams. No API key.

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | React 19 + TypeScript + Vite + Recharts |
| Backend | Python 3.12 + FastAPI |
| Data | Committed January snapshot in `data/snapshot.json` |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |

## Repository structure

```
.
├── backend/                 FastAPI app and pytest suite
│   ├── app/                 Selection, metrics, routes, snapshot loader
│   └── tests/
├── frontend/                Vite React dashboard
│   └── src/
├── data/
│   └── snapshot.json        Cached Elexon extract used by the API
├── docs/
│   └── requirements-and-assumptions.md
├── scripts/
│   ├── refresh_snapshot.py  Re-fetch and rewrite the snapshot
│   └── data_proof.py        Live one-day selection check
├── .env.example
└── README.md
```

## Local setup

### Prerequisites

- Python 3.12+
- Node.js 20+ (22 used in development)
- About 100 MB free for the virtualenv and `node_modules`

### 1. Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

Analysis endpoints (examples):

- `/api/analysis/summary`
- `/api/analysis/timeseries`
- `/api/analysis/forecast-details?start=2026-01-11T10:00:00Z`
- `/api/analysis/data-quality`

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite proxies `/api` to the backend on port 8000.

Optional: copy `.env.example` to `.env` for CORS or cutoff overrides. For a production frontend build against a separate API origin, set `VITE_API_URL` (no trailing slash). Leave it empty for same-origin / the Vite proxy.

## What the dashboard shows

- Overview for settlement deliveries **2 Jan–1 Feb 2026** (decisions **1–31 Jan 2026**)
- MAE, RMSE, and mean bias (forecast − actual), with plain-English notes
- Forecast vs actual chart; unmatched `:30` half-hours are not drawn as zero
- Signed error over time and the largest absolute misses
- Per-interval publication audit (every WINDFOR version, cutoff, selected row)
- Method and data-quality notes, including the inclusive cutoff assumption

For the full committed snapshot (fetched 28 Oct 2026): **744** matched hours, MAE about **1,995.6 MW**, RMSE about **2,498.8 MW**, MBE about **+1,728.0 MW** (overforecast on average).

Known check interval `2026-01-11T10:00:00Z`: selected publish `2026-01-10T09:30:00Z`, forecast **18,883 MW**, actual **14,789 MW**, error **+4,094 MW**.

## Refreshing the snapshot

The UI reads the committed file. It does not call Elexon on each click.

```bash
.venv/bin/python scripts/refresh_snapshot.py
```

This re-fetches FUELHH and WINDFOR for the study window, validates the response windows, and fails if look-ahead selection or error arithmetic regresses.

## Tests

```bash
.venv/bin/pytest backend/tests
cd frontend && npm test
```

## Deployment

Docker Compose and a verified public deployment are not in this repository yet. Do not treat a placeholder URL as live.

When deployed, the intended shape is:

- Static frontend on a host such as Vercel
- FastAPI reading `data/snapshot.json` (no live Elexon dependency for the dashboard)
- `VITE_API_URL` pointing at the API origin, or same-origin rewrites

## Business rules (short)

1. Delivery settlement dates: 2 Jan–1 Feb 2026, 00:00–23:30 Europe/London.
2. Cutoff: **09:50** Europe/London on the decision day (delivery − 1), inclusive. Latest eligible `publishTime` wins; tied publish times keep the lower generation.
3. Join only on equal `startTime`. WINDFOR is hourly; half-hour actuals with no forecast are excluded (`no_forecast_for_interval`), never filled with zero.
4. Error = forecast − actual. Empty matched set → metrics are null, not 0.

Full discovery notes: [`docs/requirements-and-assumptions.md`](docs/requirements-and-assumptions.md).

## AI tools used

- **Cursor** (Composer agent) for scaffolding, API wiring, tests, and UI iteration
- Live Elexon API calls and committed snapshot for verification; figures above are from that snapshot, not model-invented numbers

## Licence / data

Application code in this repository is provided for the take-home review. Generation figures come from Elexon’s public BMRS Insights API and remain subject to Elexon’s terms.
