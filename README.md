# Earth System Trend Detective

React + Tailwind CSS frontend and FastAPI backend.

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

The Vite dev server proxies `/api` to the backend, so the frontend can call `/api/health` during local development.
