# Backend

FastAPI API for the AI construction drawing review platform.

## Local start

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Health check: `GET /health`

The current backend intentionally stops at secure project/drawing/task foundations. AI analysis is not claimed until a real review worker is connected.
