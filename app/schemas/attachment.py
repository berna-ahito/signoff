from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentMeta(BaseModel):
    id: int
    filename: str
    content_type: str
    uploaded_by: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AttachmentUploadResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
