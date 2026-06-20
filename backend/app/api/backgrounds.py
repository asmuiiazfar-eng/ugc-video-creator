from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.database import get_db
from app.models import Background, User
from app.core.deps import get_current_user
from app.core.kieai import generate_background as kieai_gen_bg

router = APIRouter(prefix="/backgrounds", tags=["backgrounds"])


class BackgroundResponse(BaseModel):
    id: str
    category: str
    image_url: str
    thumbnail_url: Optional[str] = None
    is_video: bool

    model_config = {"from_attributes": True}


class GenerateBackgroundRequest(BaseModel):
    prompt: str
    category: str = "custom"


@router.get("", response_model=List[BackgroundResponse])
async def list_backgrounds(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """List available backgrounds, optionally filtered by category."""
    query = select(Background)
    if category:
        query = query.where(Background.category == category)
    query = query.order_by(Background.category)

    result = await db.execute(query)
    backgrounds = result.scalars().all()
    return [BackgroundResponse(
        id=b.id,
        category=b.category,
        image_url=b.image_url,
        thumbnail_url=b.thumbnail_url,
        is_video=b.is_video,
    ) for b in backgrounds]


@router.post("/generate", response_model=BackgroundResponse, status_code=status.HTTP_201_CREATED)
async def generate_background(
    request: GenerateBackgroundRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a background image from a text prompt using Kie.ai."""
    try:
        result = await kieai_gen_bg(request.prompt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Background generation failed: {str(e)}",
        )

    import uuid
    bg_id = str(uuid.uuid4())
    image_url = result.get("image_url", result.get("url", ""))

    background = Background(
        id=bg_id,
        category=request.category,
        image_url=image_url,
        thumbnail_url=result.get("thumbnail_url"),
        is_video=False,
    )
    db.add(background)
    await db.flush()

    return BackgroundResponse(
        id=background.id,
        category=background.category,
        image_url=background.image_url,
        thumbnail_url=background.thumbnail_url,
        is_video=background.is_video,
    )