from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timezone

from app.database import get_db
from app.models import Scene, SceneRenderStatus, BackgroundType, Project, User
from app.core.deps import get_current_user

router = APIRouter(tags=["scenes"])


class SceneCreate(BaseModel):
    scene_number: int
    text: str
    estimated_duration: Optional[float] = None
    background_id: Optional[str] = None
    background_type: Optional[str] = None
    transition: Optional[str] = None


class SceneUpdate(BaseModel):
    text: Optional[str] = None
    estimated_duration: Optional[float] = None
    background_id: Optional[str] = None
    background_type: Optional[str] = None
    transition: Optional[str] = None
    render_status: Optional[str] = None
    render_url: Optional[str] = None


class SceneResponse(BaseModel):
    id: str
    project_id: str
    scene_number: int
    text: str
    estimated_duration: Optional[float] = None
    background_id: Optional[str] = None
    background_type: Optional[str] = None
    transition: Optional[str] = None
    render_status: str
    render_url: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


def _scene_to_response(scene: Scene) -> SceneResponse:
    return SceneResponse(
        id=str(scene.id),
        project_id=str(scene.project_id),
        scene_number=scene.scene_number,
        text=scene.text,
        estimated_duration=scene.estimated_duration,
        background_id=scene.background_id,
        background_type=scene.background_type.value if hasattr(scene.background_type, "value") else scene.background_type,
        transition=scene.transition,
        render_status=scene.render_status.value if hasattr(scene.render_status, "value") else scene.render_status,
        render_url=scene.render_url,
        created_at=scene.created_at.isoformat(),
        updated_at=scene.updated_at.isoformat(),
    )


async def _verify_project_access(project_id: str, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{pid}/scenes", response_model=List[SceneResponse])
async def list_scenes(
    pid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all scenes for a project."""
    await _verify_project_access(pid, current_user, db)
    result = await db.execute(
        select(Scene)
        .where(Scene.project_id == pid)
        .order_by(Scene.scene_number)
    )
    scenes = result.scalars().all()
    return [_scene_to_response(s) for s in scenes]


@router.post("/projects/{pid}/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    pid: str,
    request: SceneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new scene in a project."""
    await _verify_project_access(pid, current_user, db)

    bg_type = None
    if request.background_type:
        try:
            bg_type = BackgroundType(request.background_type)
        except ValueError:
            bg_type = request.background_type

    scene = Scene(
        project_id=pid,
        scene_number=request.scene_number,
        text=request.text,
        estimated_duration=request.estimated_duration,
        background_id=request.background_id,
        background_type=bg_type,
        transition=request.transition,
    )
    db.add(scene)
    await db.flush()
    return _scene_to_response(scene)


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: str,
    request: SceneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a scene."""
    result = await db.execute(
        select(Scene).where(Scene.id == scene_id)
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Verify project ownership
    await _verify_project_access(str(scene.project_id), current_user, db)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "background_type" and value is not None:
            try:
                scene.background_type = BackgroundType(value)
            except ValueError:
                scene.background_type = value
        elif key == "render_status" and value is not None:
            try:
                scene.render_status = SceneRenderStatus(value)
            except ValueError:
                scene.render_status = value
        else:
            setattr(scene, key, value)
    scene.updated_at = datetime.now(timezone.utc)
    db.add(scene)
    await db.flush()
    return _scene_to_response(scene)


@router.delete("/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scene."""
    result = await db.execute(
        select(Scene).where(Scene.id == scene_id)
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    await _verify_project_access(str(scene.project_id), current_user, db)
    await db.delete(scene)
    await db.flush()


@router.post("/scenes/{scene_id}/rerender", response_model=SceneResponse)
async def rerender_scene(
    scene_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a rerender of a scene by resetting its render status."""
    result = await db.execute(
        select(Scene).where(Scene.id == scene_id)
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    await _verify_project_access(str(scene.project_id), current_user, db)

    scene.render_status = SceneRenderStatus.pending
    scene.render_url = None
    scene.updated_at = datetime.now(timezone.utc)
    db.add(scene)
    await db.flush()
    return _scene_to_response(scene)