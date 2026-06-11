import urllib.parse

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


async def _read_with_size_limit(file: UploadFile, max_size: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(65536)  # 64KB chunks
        if not chunk:
            break
        total += len(chunk)
        if total > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File exceeds 5MB limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _iter_chunks(data: bytes, chunk_size: int = 65536):
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


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
) -> AttachmentUploadResponse:
    _get_request_or_403(db, request_id, current_user)

    data = await _read_with_size_limit(file, MAX_FILE_SIZE)

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
) -> list[AttachmentMeta]:
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
) -> StreamingResponse:
    _get_request_or_403(db, request_id, current_user)

    attachment = db.get(RequestAttachment, attachment_id)
    if attachment is None or attachment.request_id != request_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )

    safe_name = urllib.parse.quote(attachment.filename, safe="")
    return StreamingResponse(
        _iter_chunks(attachment.file_data),
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"
        },
    )
