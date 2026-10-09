# Backend

FastAPI service for EarthTrend Myanmar.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

`requirements.txt` is the Render runtime install. `requirements-dev.txt` adds pytest and the boundary libraries used by `python -m app.cli ingest`.

Verify a single NASA POWER point:

```powershell
python -m app.cli verify
```

Tests:

```powershell
python -m pytest
```
