from datetime import datetime
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

class ProjectOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    model_config = {"from_attributes": True}

class DrawingOut(BaseModel):
    id: int
    project_id: int
    original_name: str
    mime_type: str
    size_bytes: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class ReviewOut(BaseModel):
    id: int
    project_id: int
    status: str
    progress: int
    error: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
