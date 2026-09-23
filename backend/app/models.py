from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    drawings = relationship("Drawing", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("ReviewTask", back_populates="project", cascade="all, delete-orphan")

class Drawing(Base):
    __tablename__ = "drawings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drawing_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discipline: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="uploaded", nullable=False)
    processing_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    project = relationship("Project", back_populates="drawings")
    pages = relationship("DrawingPage", back_populates="drawing", cascade="all, delete-orphan")

class DrawingPage(Base):
    __tablename__ = "drawing_pages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    drawing_id: Mapped[int] = mapped_column(ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    image_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    thumbnail_name: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    thumbnail_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    dpi: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="rendered", nullable=False)
    metadata_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    drawing_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    drawing_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detected_discipline: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scale_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    drawing = relationship("Drawing", back_populates="pages")
    text_items = relationship("DrawingPageText", back_populates="page", cascade="all, delete-orphan")

class DrawingPageText(Base):
    __tablename__ = "drawing_page_texts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("drawing_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    x0: Mapped[float] = mapped_column(Float, nullable=False)
    y0: Mapped[float] = mapped_column(Float, nullable=False)
    x1: Mapped[float] = mapped_column(Float, nullable=False)
    y1: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    block_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coordinate_space: Mapped[str] = mapped_column(String(20), default="source", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    page = relationship("DrawingPage", back_populates="text_items")

class ReviewTask(Base):
    __tablename__ = "review_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    project = relationship("Project", back_populates="reviews")
    issues = relationship("ReviewIssue", back_populates="review", cascade="all, delete-orphan")

class ReviewIssue(Base):
    __tablename__ = "review_issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("review_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("drawing_pages.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    x0: Mapped[float | None] = mapped_column(Float, nullable=True)
    y0: Mapped[float | None] = mapped_column(Float, nullable=True)
    x1: Mapped[float | None] = mapped_column(Float, nullable=True)
    y1: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    review = relationship("ReviewTask", back_populates="issues")
    page = relationship("DrawingPage")
