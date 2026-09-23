from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("项目名称不能为空")
        return value

class ProjectOut(BaseModel):
    id: int; name: str; created_at: datetime
    model_config = {"from_attributes": True}

class DrawingPageTextOut(BaseModel):
    id: int; page_id: int; text: str
    x0: float; y0: float; x1: float; y1: float
    confidence: float | None; source: str
    block_no: int | None; line_no: int | None; word_no: int | None
    created_at: datetime
    model_config = {"from_attributes": True}

class DrawingPageSummaryOut(BaseModel):
    id: int; drawing_id: int; page_number: int; image_name: str
    thumbnail_name: str | None; thumbnail_width: int | None; thumbnail_height: int | None
    width: int; height: int; dpi: int; status: str; metadata_status: str
    extracted_text: str | None; drawing_number: str | None; drawing_title: str | None
    detected_discipline: str | None; scale_text: str | None; created_at: datetime
    model_config = {"from_attributes": True}

class DrawingPageOut(BaseModel):
    id: int; drawing_id: int; page_number: int; image_name: str
    thumbnail_name: str | None; thumbnail_width: int | None; thumbnail_height: int | None
    width: int; height: int; dpi: int; status: str; metadata_status: str
    extracted_text: str | None; drawing_number: str | None; drawing_title: str | None
    detected_discipline: str | None; scale_text: str | None; created_at: datetime
    text_items: list[DrawingPageTextOut] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class DrawingOut(BaseModel):
    id: int; project_id: int; original_name: str; mime_type: str; size_bytes: int; sha256: str
    page_count: int | None; drawing_number: str | None; discipline: str | None; status: str
    processing_progress: int; error: str | None; created_at: datetime
    pages: list[DrawingPageOut] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class ReviewIssueOut(BaseModel):
    id: int; review_id: int; page_id: int | None
    rule_id: str; category: str; severity: str; title: str; description: str
    evidence: str | None; confidence: float | None
    x0: float | None; y0: float | None; x1: float | None; y1: float | None
    coordinate_space: str
    status: str; created_at: datetime
    model_config = {"from_attributes": True}

class ReviewOut(BaseModel):
    id: int; project_id: int; status: str; progress: int; error: str | None
    attempts: int; started_at: datetime | None; finished_at: datetime | None; created_at: datetime
    model_config = {"from_attributes": True}

class ReviewDetailOut(ReviewOut):
    issues: list[ReviewIssueOut] = Field(default_factory=list)
    model_config = {"from_attributes": True}
