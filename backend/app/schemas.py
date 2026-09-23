from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("项目名称不能为空")
        return value

class ProjectOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    model_config = {"from_attributes": True}

class DrawingPageOut(BaseModel):
    id: int
    drawing_id: int
    page_number: int
    image_name: str
    width: int
    height: int
    dpi: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class DrawingOut(BaseModel):
    id: int
    project_id: int
    original_name: str
    mime_type: str
    size_bytes: int
    sha256: str
    page_count: int | None
    drawing_number: str | None
    discipline: str | None
    status: str
    created_at: datetime
    pages: list[DrawingPageOut] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class ReviewOut(BaseModel):
    id: int
    project_id: int
    status: str
    progress: int
    error: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
