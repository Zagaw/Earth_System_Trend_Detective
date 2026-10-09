# EarthTrend Myanmar

Climate-trend application for Myanmar. The frontend is React, TypeScript, Vite, and Tailwind CSS. The API is FastAPI. Scientific results come from NASA POWER after ingestion and tested analysis; this version verifies the source parameters and does not show trend numbers yet.

## What works now

- NASA POWER download for rainfall, temperature, and humidity, split into the 10 degree tiles the API allows.
- Myanmar mask from geoBoundaries. 190 grid cells are inside the country.
- Annual and seasonal aggregation, Sen's slope, Mann–Kendall with a Hamed–Rao correction when residuals are autocorrelated, and Benjamini–Hochberg adjustment across grid cells and across states.
- Dashboard, trend page, map, region comparison, impact and anomaly page, and CSV/GeoJSON export.
- Plain-language text is filled from those calculated fields.

## Build the local dataset

The processed file is created on this machine and is not committed.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.cli ingest
```

The current local dataset covers January 2001 through December 2025.

Verified units are in [docs/data-dictionary.md](docs/data-dictionary.md).

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000

Docs: http://127.0.0.1:8000/docs

Check one live point without saving a national dataset:

```powershell
python -m app.cli verify
```

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest
```

```powershell
cd frontend
npm run typecheck
npm run build
```

Analysis libraries (Xarray, GeoPandas, PyMannKendall, and the rest) are listed under the `analysis` extra in `backend/pyproject.toml`. They are not installed yet.
