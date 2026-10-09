# Backend

FastAPI service for EarthTrend Myanmar.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Verify a single NASA POWER point:

```powershell
python -m app.cli verify
```

Tests:

```powershell
python -m pytest
```
