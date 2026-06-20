from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.database import get_db
from app.models import Voice
from app.core.deps import get_current_user

router = APIRouter(prefix="/voices", tags=["voices"])


class VoiceResponse(BaseModel):
    id: str
    name: str
    gender: Optional[str] = None
    tone: Optional[str] = None
    audio_url: Optional[str] = None
    preview_url: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=List[VoiceResponse])
async def list_voices(
    db: AsyncSession = Depends(get_db),
):
    """List all active voices."""
    result = await db.execute(
        select(Voice).where(Voice.is_active == True)
    )
    voices = result.scalars().all()
    return [VoiceResponse(
        id=v.id,
        name=v.name,
        gender=v.gender,
        tone=v.tone,
        audio_url=v.audio_url,
        preview_url=v.preview_url,
        is_active=v.is_active,
    ) for v in voices]


@router.get("/{voice_id}/preview", response_model=VoiceResponse)
async def get_voice_preview(
    voice_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific voice with its preview URL."""
    result = await db.execute(select(Voice).where(Voice.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return VoiceResponse(
        id=voice.id,
        name=voice.name,
        gender=voice.gender,
        tone=voice.tone,
        audio_url=voice.audio_url,
        preview_url=voice.preview_url,
        is_active=voice.is_active,
    )