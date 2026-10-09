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
pip install -r requirements-dev.txt
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

Analysis libraries (Xarray, GeoPandas, PyMannKendall, and the rest) are listed under the `analysis` extra in `backend/pyproject.toml`. The Render service installs `backend/requirements.txt`. Local ingest and tests use `backend/requirements-dev.txt`.

## Deploy

Deploy the API on Render and the React app on Vercel. The browser calls Render directly, so the Vercel site needs the Render URL at build time, and Render must allow that Vercel origin.

Commit `backend/data/processed/climate_monthly.nc` and `backend/data/processed/regions.json` before connecting Render. Those files are the dataset the API serves. Do not commit `backend/.env` or `backend/data/raw`.

### Render

1. Push the repository, including the two processed data files.
2. In Render, create a Blueprint from `render.yaml`, or create a Python web service with root directory `backend`.
3. Build command: `pip install --upgrade pip && pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Health check: `/api/v1/health`
6. Set `UNDERSTAND_AI_API_KEY` only if the Understand replies should use OpenRouter. Leave it empty to keep the calculated explanations.
7. After Vercel has a URL, you can replace `CORS_ORIGINS` with that exact origin, such as `https://your-app.vercel.app`. The blueprint already allows `https://*.vercel.app`.

The service URL will look like `https://earthtrend-myanmar-api.onrender.com`.

### Vercel

1. Import the same repository.
2. Set the root directory to `frontend`.
3. Framework preset: Vite. Build command: `npm run build`. Output directory: `dist`.
4. Add this environment variable, then deploy:

```text
VITE_API_BASE_URL=https://earthtrend-myanmar-api.onrender.com/api/v1
```

Use the real Render hostname and do not add a trailing slash. If you change this value later, redeploy the frontend. Vite locks the API address into the build.
