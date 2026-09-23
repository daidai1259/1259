# Backend

FastAPI API for the AI construction drawing review platform.

## Local start

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Health check: `GET /health`

## Database

Schema changes are managed by Alembic. The API does **not** create or modify database tables automatically at startup.

After pulling new backend changes, run:

```powershell
alembic upgrade head
```

To inspect migration state:

```powershell
alembic current
alembic history
```

The current backend provides secure project/drawing ingestion, PDF page rendering, thumbnails, PDF text extraction with coordinates, and review-task foundations. OCR for scanned drawings and the actual AI review worker are intentionally not claimed until their providers are connected and tested.

The system is intended for AI-assisted review and does not replace licensed engineers, statutory drawing-review organizations, or legal approval.
