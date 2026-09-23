from pathlib import Path
import shutil
from uuid import uuid4
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from .config import settings
from .db import SessionLocal, get_db
from .models import Drawing, DrawingPage, DrawingPageText, Project, ReviewTask, ReviewIssue
from .metadata import extract_image_metadata, extract_pdf_page_metadata, extract_pdf_page_text_items
from .processing import FileInspectionError, inspect_file
from .rendering import RenderingError, create_thumbnail, render_pdf, validate_image_dimensions
from .review import run_review
from .schemas import DrawingOut, DrawingPageOut, ProjectCreate, ProjectOut, ReviewDetailOut, ReviewOut

UPLOAD_ROOT = Path(settings.upload_dir).resolve()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
PAGES_ROOT = UPLOAD_ROOT / "pages"
PAGES_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI施工图审核平台 API", version="0.5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
ALLOWED_TYPES = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}

def _page_path(drawing_id: int, filename: str) -> Path:
    page_dir = (PAGES_ROOT / str(drawing_id)).resolve()
    path = (page_dir / filename).resolve()
    if page_dir not in path.parents:
        raise HTTPException(400, "页面文件路径非法")
    return path

def process_drawing(drawing_id: int) -> None:
    db = SessionLocal()
    drawing = None
    page_dir = PAGES_ROOT / str(drawing_id)
    try:
        drawing = db.get(Drawing, drawing_id)
        if not drawing:
            return
        drawing.status = "processing"
        drawing.processing_progress = 5
        drawing.error = None
        db.commit()

        source = UPLOAD_ROOT / drawing.stored_name
        page_dir.mkdir(parents=True, exist_ok=True)
        if drawing.mime_type == "application/pdf":
            pages = render_pdf(source, page_dir)
        else:
            image_name = f"page-0001{source.suffix.lower()}"
            target = page_dir / image_name
            shutil.copyfile(source, target)
            width, height = validate_image_dimensions(target)
            pages = [{"page_number": 1, "image_name": image_name, "width": width, "height": height, "dpi": 0}]

        drawing.processing_progress = 80
        db.commit()

        for item in pages:
            source_page = page_dir / item["image_name"]
            thumbnail_name = f"thumb-{item['page_number']:04d}.jpg"
            thumbnail_path = page_dir / thumbnail_name
            thumb_width, thumb_height = create_thumbnail(source_page, thumbnail_path)

            if drawing.mime_type == "application/pdf":
                metadata = extract_pdf_page_metadata(source, item["page_number"], drawing.original_name)
                text_items = extract_pdf_page_text_items(source, item["page_number"])
            else:
                metadata = extract_image_metadata(source_page, drawing.original_name)
                text_items = []

            page = DrawingPage(
                drawing_id=drawing.id,
                thumbnail_name=thumbnail_name,
                thumbnail_width=thumb_width,
                thumbnail_height=thumb_height,
                metadata_status="ready",
                **metadata,
                **item,
            )
            db.add(page)
            db.flush()

            for text_item in text_items:
                db.add(DrawingPageText(page_id=page.id, **text_item))

        drawing.page_count = len(pages)
        drawing.processing_progress = 100
        drawing.status = "ready"
        db.commit()
    except (RenderingError, OSError) as exc:
        db.rollback()
        drawing = db.get(Drawing, drawing_id)
        if drawing:
            drawing.status = "failed"
            drawing.processing_progress = 100
            drawing.error = str(exc)[:1000]
            db.commit()
        if page_dir.exists():
            for path in page_dir.iterdir():
                if path.is_file():
                    path.unlink(missing_ok=True)
    except Exception:
        db.rollback()
        drawing = db.get(Drawing, drawing_id)
        if drawing:
            drawing.status = "failed"
            drawing.processing_progress = 100
            drawing.error = "图纸处理失败"
            db.commit()
        if page_dir.exists():
            for path in page_dir.iterdir():
                if path.is_file():
                    path.unlink(missing_ok=True)
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "service": "construction-review-api", "version": app.version}

@app.post("/api/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()

@app.post("/api/projects/{project_id}/drawings", response_model=DrawingOut, status_code=202)
async def upload_drawing(project_id: int, background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
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
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(413, f"文件不能超过 {settings.max_upload_mb}MB")
                output.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except OSError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(500, "文件保存失败") from exc
    finally:
        await file.close()

    original_name = (file.filename or "unnamed").replace("\\", "/").split("/")[-1][:255]
    try:
        metadata = inspect_file(destination, original_name, file.content_type)
    except FileInspectionError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(415, str(exc)) from exc

    drawing = Drawing(
        project_id=project_id,
        original_name=original_name,
        stored_name=stored_name,
        mime_type=file.content_type,
        size_bytes=total,
        sha256=metadata["sha256"],
        page_count=metadata["page_count"],
        discipline=metadata["discipline"],
        status="queued",
        processing_progress=0,
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    background_tasks.add_task(process_drawing, drawing.id)
    return drawing

@app.get("/api/projects/{project_id}/drawings", response_model=list[DrawingOut])
def list_drawings(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    return (
        db.query(Drawing)
        .options(selectinload(Drawing.pages).selectinload(DrawingPage.text_items))
        .filter(Drawing.project_id == project_id)
        .order_by(Drawing.id.desc())
        .all()
    )

@app.get("/api/drawings/{drawing_id}", response_model=DrawingOut)
def get_drawing(drawing_id: int, db: Session = Depends(get_db)):
    drawing = (
        db.query(Drawing)
        .options(selectinload(Drawing.pages).selectinload(DrawingPage.text_items))
        .filter(Drawing.id == drawing_id)
        .first()
    )
    if not drawing:
        raise HTTPException(404, "图纸不存在")
    return drawing

@app.get("/api/drawings/{drawing_id}/pages", response_model=list[DrawingPageOut])
def list_pages(drawing_id: int, db: Session = Depends(get_db)):
    if not db.get(Drawing, drawing_id):
        raise HTTPException(404, "图纸不存在")
    return (
        db.query(DrawingPage)
        .options(selectinload(DrawingPage.text_items))
        .filter(DrawingPage.drawing_id == drawing_id)
        .order_by(DrawingPage.page_number)
        .all()
    )

@app.get("/api/drawing-pages/{page_id}/image")
def get_page_image(page_id: int, db: Session = Depends(get_db)):
    page = db.get(DrawingPage, page_id)
    if not page:
        raise HTTPException(404, "图纸页面不存在")
    path = _page_path(page.drawing_id, page.image_name)
    if not path.is_file():
        raise HTTPException(404, "页面图像文件不存在")
    media = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(path, media_type=media, filename=page.image_name)

@app.get("/api/drawing-pages/{page_id}/thumbnail")
def get_page_thumbnail(page_id: int, db: Session = Depends(get_db)):
    page = db.get(DrawingPage, page_id)
    if not page or not page.thumbnail_name:
        raise HTTPException(404, "缩略图不存在")
    path = _page_path(page.drawing_id, page.thumbnail_name)
    if not path.is_file():
        raise HTTPException(404, "缩略图文件不存在")
    return FileResponse(path, media_type="image/jpeg", filename=page.thumbnail_name)

@app.post("/api/projects/{project_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    if db.query(Drawing).filter(Drawing.project_id == project_id, Drawing.status == "ready").count() == 0:
        raise HTTPException(400, "请等待图纸处理完成后再开始审核")
    task = ReviewTask(project_id=project_id, status="queued", progress=0)
    db.add(task)
    db.commit()
    db.refresh(task)
    background_tasks.add_task(_run_review_background, task.id)
    return task

def _run_review_background(review_id: int) -> None:
    db = SessionLocal()
    try:
        run_review(review_id, db)
    finally:
        db.close()

@app.post("/api/reviews/{review_id}/retry", response_model=ReviewOut)
def retry_review(review_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.get(ReviewTask, review_id)
    if not task:
        raise HTTPException(404, "审核任务不存在")
    if task.status != "failed":
        raise HTTPException(409, "只有失败的审核任务可以重试")
    task.status = "retry"
    task.progress = 0
    task.error = None
    db.commit()
    db.refresh(task)
    background_tasks.add_task(_run_review_background, task.id)
    return task

@app.get("/api/reviews/{review_id}", response_model=ReviewDetailOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    task = db.query(ReviewTask).options(selectinload(ReviewTask.issues)).filter(ReviewTask.id == review_id).first()
    if not task:
        raise HTTPException(404, "审核任务不存在")
    return task
