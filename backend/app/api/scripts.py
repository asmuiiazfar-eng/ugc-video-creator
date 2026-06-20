from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_current_user
from app.core.script_gen import generate_script as gen_script, split_script as split_script_fn

router = APIRouter(prefix="/scripts", tags=["scripts"])


class GenerateScriptRequest(BaseModel):
    product_name: str
    description: str
    audience: str = "general"
    tone: str = "professional"
    duration: int = 60


class SplitScriptRequest(BaseModel):
    script_text: str


@router.post("/generate")
async def generate_script(request: GenerateScriptRequest):
    """Generate a video script using Kie.ai LLM."""
    try:
        result = await gen_script(
            product_name=request.product_name,
            description=request.description,
            audience=request.audience,
            tone=request.tone,
            duration=request.duration,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Script generation failed: {str(e)}",
        )


@router.post("/split")
async def split_script(request: SplitScriptRequest):
    """Parse a raw script text into structured scenes."""
    try:
        result = await split_script_fn(request.script_text)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Script splitting failed: {str(e)}",
        )