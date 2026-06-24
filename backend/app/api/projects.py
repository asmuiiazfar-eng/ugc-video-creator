from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timezone

from app.database import get_db
from app.models import Project, ProjectStatus, User, Scene
from app.core.deps import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    title: str
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    voice_speed: Optional[float] = 1.0
    voice_pitch: Optional[str] = "normal"
    duration_seconds: Optional[int] = None
    script_raw: Optional[str] = None
    scenes: Optional[list[dict]] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    voice_speed: Optional[float] = None
    voice_pitch: Optional[str] = None
    thumbnail_url: Optional[str] = None
    output_url: Optional[str] = None
    duration_seconds: Optional[int] = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    status: str
    duration_seconds: Optional[int] = None
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    voice_speed: Optional[float] = None
    voice_pitch: Optional[str] = None
    thumbnail_url: Optional[str] = None
    output_url: Optional[str] = None
    credit_cost: Optional[int] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


def _project_response(project: Project) -> ProjectResponse:
    """Build a ProjectResponse from a Project ORM object."""
    return ProjectResponse(
        id=str(project.id),
        user_id=str(project.user_id),
        title=project.title,
        status=project.status.value if hasattr(project.status, "value") else project.status,
        duration_seconds=project.duration_seconds,
        avatar_id=str(project.avatar_id) if project.avatar_id else None,
        voice_id=project.voice_id,
        voice_speed=project.voice_speed,
        voice_pitch=project.voice_pitch,
        thumbnail_url=project.thumbnail_url,
        output_url=project.output_url,
        credit_cost=project.credit_cost,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current user."""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )
    projects = result.scalars().all()
    return [_project_response(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project (optionally with scenes in one call)."""
    project = Project(
        title=request.title,
        user_id=current_user.id,
        avatar_id=request.avatar_id,
        voice_id=request.voice_id,
        voice_speed=request.voice_speed,
        voice_pitch=request.voice_pitch,
        duration_seconds=request.duration_seconds,
    )
    db.add(project)
    await db.flush()

    # Persist scenes passed inline from the wizard (Issue 4 contract fix)
    if request.scenes:
        for idx, scene_data in enumerate(request.scenes):
            scene = Scene(
                project_id=project.id,
                scene_number=scene_data.get("scene_number", idx + 1),
                text=scene_data.get("text", ""),
                estimated_duration=float(scene_data.get("duration_seconds", 0) or 0),
                background_id=scene_data.get("background_id"),
                transition=scene_data.get("transition", "fade"),
            )
            db.add(scene)
        await db.flush()

    return _project_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single project by ID."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status" and value is not None:
            try:
                project.status = ProjectStatus(value)
            except ValueError:
                project.status = value
        else:
            setattr(project, key, value)
    project.updated_at = datetime.now(timezone.utc)
    db.add(project)
    await db.flush()
    return _project_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.flush()


# ─── Issue 1: Render trigger endpoint ──────────────────────────────
@router.post("/{project_id}/render", status_code=status.HTTP_202_ACCEPTED)
async def trigger_render(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dispatch the Celery render task for a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")

    # Import locally to avoid celery import at module load
    from app.workers.render_tasks import render_project

    task = render_project.delay(str(project.id))
    return {"render_id": task.id, "project_id": str(project.id), "status": "queued"}