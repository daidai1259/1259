from pathlib import Path
from uuid import uuid4
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, get_db
from .models import Drawing, Project, ReviewTask
from .schemas import DrawingOut, ProjectCreate, ProjectOut, ReviewOut

UPLOAD_ROOT = Path(settings.upload_dir).resolve()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI施工图审核平台 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ALLOWED_TYPES = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "construction-review-api"}

@app.post("/api/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, "项目名称不能为空")
    project = Project(name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()

@app.post("/api/projects/{project_id}/drawings", response_model=DrawingOut, status_code=201)
async def upload_drawing(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "仅支持 PDF、JPG、PNG")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    suffix = ALLOWED_TYPES[file.content_type]
    stored_name = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_ROOT / stored_name
    total = 0

    try:
        with destination.open("xb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(413, f"文件不能超过 {settings.max_upload_mb}MB")
                output.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except OSError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(500, f"文件保存失败: {exc}") from exc
    finally:
        await file.close()

    drawing = Drawing(
        project_id=project_id,
        original_name=(file.filename or "unnamed").replace("\\", "/").split("/")[-1][:255],
        stored_name=stored_name,
        mime_type=file.content_type,
        size_bytes=total,
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return drawing

@app.get("/api/projects/{project_id}/drawings", response_model=list[DrawingOut])
def list_drawings(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    return db.query(Drawing).filter(Drawing.project_id == project_id).order_by(Drawing.id.desc()).all()

@app.post("/api/projects/{project_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    if db.query(Drawing).filter(Drawing.project_id == project_id).count() == 0:
        raise HTTPException(400, "请先上传至少一张施工图")
    task = ReviewTask(project_id=project_id, status="queued", progress=0)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/api/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    task = db.get(ReviewTask, review_id)
    if not task:
        raise HTTPException(404, "审核任务不存在")
    return task
