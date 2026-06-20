from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.database import get_db
from app.models import Avatar, User
from app.core.deps import get_current_user
from app.core.storage import get_presigned_url
from app.core.kieai import generate_avatar as kieai_generate_avatar

router = APIRouter(prefix="/avatars", tags=["avatars"])


class AvatarResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    source_photo_url: str
    avatar_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_preset: bool
    created_at: str

    model_config = {"from_attributes": True}


class UploadUrlResponse(BaseModel):
    presigned_url: str
    key: str


class GenerateAvatarRequest(BaseModel):
    source_photo_url: str


@router.get("", response_model=List[AvatarResponse])
async def list_avatars(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available avatars (user's own + presets)."""
    result = await db.execute(
        select(Avatar).where(
            (Avatar.user_id == current_user.id) | (Avatar.is_preset == True)
        ).order_by(Avatar.created_at.desc())
    )
    avatars = result.scalars().all()
    return [AvatarResponse(
        id=str(a.id),
        user_id=str(a.user_id) if a.user_id else None,
        source_photo_url=a.source_photo_url,
        avatar_url=a.avatar_url,
        thumbnail_url=a.thumbnail_url,
        is_preset=a.is_preset,
        created_at=a.created_at.isoformat(),
    ) for a in avatars]


@router.post("/upload", response_model=UploadUrlResponse)
async def get_upload_url(
    current_user: User = Depends(get_current_user),
):
    """Get a presigned URL for uploading an avatar source photo."""
    import uuid
    key = f"avatars/{current_user.id}/{uuid.uuid4()}.jpg"
    url = await get_presigned_url(key, expires_in=3600)
    return UploadUrlResponse(presigned_url=url, key=key)


@router.post("/generate", response_model=AvatarResponse)
async def generate_avatar(
    request: GenerateAvatarRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an avatar from a source photo using Kie.ai."""
    try:
        result = await kieai_generate_avatar(request.source_photo_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avatar generation failed: {str(e)}",
        )

    avatar_url = result.get("avatar_url", "")
    thumbnail_url = result.get("thumbnail_url", "")

    avatar = Avatar(
        user_id=current_user.id,
        source_photo_url=request.source_photo_url,
        avatar_url=avatar_url,
        thumbnail_url=thumbnail_url or None,
        is_preset=False,
    )
    db.add(avatar)
    await db.flush()

    return AvatarResponse(
        id=str(avatar.id),
        user_id=str(avatar.user_id),
        source_photo_url=avatar.source_photo_url,
        avatar_url=avatar.avatar_url,
        thumbnail_url=avatar.thumbnail_url,
        is_preset=avatar.is_preset,
        created_at=avatar.created_at.isoformat(),
    )