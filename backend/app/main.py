from pathlib import Path
from uuid import uuid4
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from .config import settings
from .db import Base, engine, get_db
from .models import Drawing, DrawingPage, Project, ReviewTask
from .processing import FileInspectionError, inspect_file
from .rendering import RenderingError, render_pdf, validate_image_dimensions
from .schemas import DrawingOut, DrawingPageOut, ProjectCreate, ProjectOut, ReviewOut

UPLOAD_ROOT = Path(settings.upload_dir).resolve()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
PAGES_ROOT = UPLOAD_ROOT / "pages"
PAGES_ROOT.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI施工图审核平台 API", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["*"])
ALLOWED_TYPES = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "construction-review-api", "version": app.version}

@app.post("/api/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name); db.add(project); db.commit(); db.refresh(project); return project

@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()

@app.post("/api/projects/{project_id}/drawings", response_model=DrawingOut, status_code=201)
async def upload_drawing(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not db.get(Project, project_id): raise HTTPException(404, "项目不存在")
    if file.content_type not in ALLOWED_TYPES: raise HTTPException(415, "仅支持 PDF、JPG、PNG")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    suffix = ALLOWED_TYPES[file.content_type]; stored_name = f"{uuid4().hex}{suffix}"; destination = UPLOAD_ROOT / stored_name
    total = 0
    try:
        with destination.open("xb") as output:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes: raise HTTPException(413, f"文件不能超过 {settings.max_upload_mb}MB")
                output.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True); raise
    except OSError as exc:
        destination.unlink(missing_ok=True); raise HTTPException(500, "文件保存失败") from exc
    finally:
        await file.close()
    original_name = (file.filename or "unnamed").replace("\\", "/").split("/")[-1][:255]
    try:
        metadata = inspect_file(destination, original_name, file.content_type)
    except FileInspectionError as exc:
        destination.unlink(missing_ok=True); raise HTTPException(415, str(exc)) from exc

    drawing = Drawing(project_id=project_id, original_name=original_name, stored_name=stored_name, mime_type=file.content_type, size_bytes=total, sha256=metadata["sha256"], page_count=metadata["page_count"], discipline=metadata["discipline"], status="processing")
    db.add(drawing); db.commit(); db.refresh(drawing)

    page_dir = PAGES_ROOT / str(drawing.id)
    try:
        if metadata["kind"] == "pdf":
            pages = render_pdf(destination, page_dir)
        else:
            page_dir.mkdir(parents=True, exist_ok=True)
            image_name = f"page-0001{destination.suffix.lower()}"
            target = page_dir / image_name
            target.write_bytes(destination.read_bytes())
            width, height = validate_image_dimensions(target)
            pages = [{"page_number": 1, "image_name": image_name, "width": width, "height": height, "dpi": 0}]
        for item in pages:
            db.add(DrawingPage(drawing_id=drawing.id, **item))
        drawing.status = "ready"; drawing.page_count = len(pages); db.commit()
        db.refresh(drawing)
    except RenderingError as exc:
        db.rollback(); drawing.status = "failed"; db.add(drawing); db.commit()
        raise HTTPException(422, str(exc)) from exc
    return db.query(Drawing).options(selectinload(Drawing.pages)).filter(Drawing.id == drawing.id).one()

@app.get("/api/projects/{project_id}/drawings", response_model=list[DrawingOut])
def list_drawings(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id): raise HTTPException(404, "项目不存在")
    return db.query(Drawing).options(selectinload(Drawing.pages)).filter(Drawing.project_id == project_id).order_by(Drawing.id.desc()).all()

@app.get("/api/drawings/{drawing_id}/pages", response_model=list[DrawingPageOut])
def list_pages(drawing_id: int, db: Session = Depends(get_db)):
    if not db.get(Drawing, drawing_id): raise HTTPException(404, "图纸不存在")
    return db.query(DrawingPage).filter(DrawingPage.drawing_id == drawing_id).order_by(DrawingPage.page_number).all()

@app.get("/api/drawing-pages/{page_id}/image")
def get_page_image(page_id: int, db: Session = Depends(get_db)):
    page = db.get(DrawingPage, page_id)
    if not page: raise HTTPException(404, "图纸页面不存在")
    path = PAGES_ROOT / str(page.drawing_id) / page.image_name
    if not path.is_file(): raise HTTPException(404, "页面图像文件不存在")
    return FileResponse(path, media_type="image/png" if path.suffix.lower()==".png" else "image/jpeg", filename=page.image_name)

@app.post("/api/projects/{project_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id): raise HTTPException(404, "项目不存在")
    if db.query(Drawing).filter(Drawing.project_id == project_id).count() == 0: raise HTTPException(400, "请先上传至少一张施工图")
    task = ReviewTask(project_id=project_id, status="queued", progress=0); db.add(task); db.commit(); db.refresh(task); return task

@app.get("/api/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    task = db.get(ReviewTask, review_id)
    if not task: raise HTTPException(404, "审核任务不存在")
    return task
