# Frontend

React, TypeScript, Vite, and Tailwind CSS for EarthTrend Myanmar.

```powershell
npm install
npm run dev
```

The dev server proxies `/api` to FastAPI on port 8000. Set `VITE_API_BASE_URL` to override the default `/api/v1`.

On Vercel, set the project root to this folder and set `VITE_API_BASE_URL` to the Render API, including `/api/v1`, before the production build.
