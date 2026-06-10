import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import _get_request_or_403, get_current_active_user
from app.db.base import get_db
from app.db.models import RequestAttachment, User
from app.schemas.attachment import AttachmentMeta, AttachmentUploadResponse

router = APIRouter(prefix="/requests", tags=["attachments"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_FILES_PER_REQUEST = 5


@router.post(
    "/{request_id}/attachments",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    request_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _get_request_or_403(db, request_id, current_user)

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 5MB limit",
        )

    existing_count = (
        db.query(RequestAttachment)
        .filter(RequestAttachment.request_id == request_id)
        .count()
    )
    if existing_count >= MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 5 attachments per request reached",
        )

    attachment = RequestAttachment(
        request_id=request_id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        file_data=data,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return AttachmentUploadResponse.model_validate(attachment)


@router.get("/{request_id}/attachments", response_model=list[AttachmentMeta])
def list_attachments(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _get_request_or_403(db, request_id, current_user)

    attachments = (
        db.query(RequestAttachment)
        .filter(RequestAttachment.request_id == request_id)
        .all()
    )
    return [AttachmentMeta.model_validate(a) for a in attachments]


@router.get("/{request_id}/attachments/{attachment_id}/download")
def download_attachment(
    request_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _get_request_or_403(db, request_id, current_user)

    attachment = db.get(RequestAttachment, attachment_id)
    if attachment is None or attachment.request_id != request_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )

    return StreamingResponse(
        io.BytesIO(attachment.file_data),
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"'
        },
    )
