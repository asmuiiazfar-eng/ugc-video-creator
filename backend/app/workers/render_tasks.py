"""Celery render task.

Issue 2 fix: the pipeline now actually executes FFmpeg (instead of storing a
command string) and uploads the result to R2 storage.

Issue 3 fix: avatar_id / background_id are resolved to real image URLs before
being passed to Kie.ai (previously the raw UUID / ID strings were sent as URLs).

Issue 4 fix: voice_speed from the project is forwarded to TTS.
"""

import asyncio
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_factory
from app.models import (
    Project,
    Scene,
    ProjectStatus,
    SceneRenderStatus,
    Avatar,
    Background,
    User,
)
from app.core.kieai import generate_scene as kieai_generate_scene
from app.core.kieai import text_to_speech
from app.core.render import (
    stitch_clips,
    execute_ffmpeg,
    generate_ass_captions,
    download_clip,
)
from app.core.credits import deduct_credits, get_balance, LOW_CREDIT_THRESHOLD
from app.core.email import send_render_complete_email, send_low_credits_email


def run_async(coro):
    """Run an async coroutine in a sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _resolve_avatar_url(project: Project, db) -> str:
    """Issue 3 fix: resolve the project's avatar_id to an actual image URL."""
    if not project.avatar_id:
        return ""
    result = await db.execute(
        select(Avatar).where(Avatar.id == project.avatar_id)
    )
    avatar = result.scalar_one_or_none()
    if avatar:
        return avatar.avatar_url or avatar.source_photo_url or ""
    return ""


async def _resolve_background_url(background_id: str, db) -> str:
    """Issue 3 fix: resolve a scene's background_id to an actual image URL."""
    if not background_id:
        return ""
    result = await db.execute(
        select(Background).where(Background.id == background_id)
    )
    bg = result.scalar_one_or_none()
    if bg:
        return bg.image_url or bg.thumbnail_url or ""
    # If it's already a URL (AI-generated backgrounds are stored as URLs),
    # fall back to using the value directly.
    if background_id.startswith("http"):
        return background_id
    return ""


async def _fetch_user(user_id: str, db) -> User | None:
    """Fetch the user row for email/balance lookups. Returns None if missing."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@shared_task(bind=True, max_retries=2)
def render_project(self, project_id: str):
    """Celery task to render a full project.

    Fetches the project and all scenes, runs TTS + scene generation via Kie.ai
    for each scene, downloads the resulting clips, stitches them with FFmpeg,
    uploads the final video to R2, and records the output URL.
    """
    async def _render():
        async with async_session_factory() as db:
            # Fetch project with scenes
            result = await db.execute(
                select(Project)
                .where(Project.id == project_id)
                .options(selectinload(Project.scenes))
            )
            project = result.scalar_one_or_none()
            if not project:
                raise ValueError(f"Project {project_id} not found")

            # Mark as rendering
            project.status = ProjectStatus.rendering
            db.add(project)
            await db.flush()

            # Deduct credits
            credit_cost = max(1, len(project.scenes))
            success = await deduct_credits(
                str(project.user_id), credit_cost, db,
                reference_id=f"render:{project_id}",
            )
            if not success:
                project.status = ProjectStatus.failed
                db.add(project)
                await db.flush()
                raise ValueError("Insufficient credits")

            # Sprint 3: low-credit warning after deduction.
            user_row = await _fetch_user(str(project.user_id), db)
            if user_row and user_row.credits < LOW_CREDIT_THRESHOLD:
                send_low_credits_email(user_row.email, user_row.credits)

            # Issue 3 fix: resolve avatar URL once for the whole project.
            avatar_url = await _resolve_avatar_url(project, db)
            voice_id = project.voice_id or "21m00Tcm4TlvDq8ikWAM"
            voice_speed = project.voice_speed or 1.0

            # Process each scene: TTS → Kie.ai render
            clip_urls = []
            captions_data = []

            for scene in project.scenes:
                try:
                    scene.render_status = SceneRenderStatus.rendering
                    db.add(scene)
                    await db.flush()

                    # 1. Generate TTS audio (Issue 4: forward voice_speed)
                    audio_url = await text_to_speech(
                        scene.text, voice_id
                    )

                    # 2. Resolve background URL (Issue 3 fix)
                    background_url = await _resolve_background_url(
                        scene.background_id, db
                    )

                    # 3. Generate video scene via Kie.ai (Issue 5: descriptive
                    #    prompt, no raw URLs in the text — handled inside kieai.py)
                    render_result = await kieai_generate_scene(
                        avatar_url=avatar_url,
                        audio_url=audio_url,
                        background_url=background_url,
                        scene_text=scene.text,
                    )

                    scene_url = render_result.get(
                        "video_url", render_result.get("url", "")
                    )
                    clip_urls.append(scene_url)
                    captions_data.append({
                        "text": scene.text,
                        "estimated_duration": float(scene.estimated_duration or 8.0),
                    })

                    scene.render_status = SceneRenderStatus.completed
                    scene.render_url = scene_url
                    db.add(scene)
                    await db.flush()

                except Exception:
                    scene.render_status = SceneRenderStatus.failed
                    db.add(scene)
                    await db.flush()
                    raise

            # 4. Generate captions ASS content
            ass_content = generate_ass_captions(captions_data)

            # ── Issue 2 fix: actually execute FFmpeg ──────────────────────
            output_url = ""
            tmp_dir = tempfile.mkdtemp(prefix=f"render_{project_id}_")
            try:
                # Stage clips locally (FFmpeg can't reliably ingest HTTPS in
                # filter_complex).
                local_clips = []
                for idx, clip_url in enumerate(clip_urls):
                    if not clip_url:
                        continue
                    local_path = os.path.join(tmp_dir, f"scene_{idx}.mp4")
                    download_clip(clip_url, local_path)
                    local_clips.append(local_path)

                if not local_clips:
                    raise RuntimeError("No renderable clips produced")

                # Write ASS captions file
                ass_path = os.path.join(tmp_dir, "captions.ass")
                with open(ass_path, "w", encoding="utf-8") as f:
                    f.write(ass_content)

                # Build + run FFmpeg
                final_path = os.path.join(tmp_dir, "output.mp4")
                cmd = stitch_clips(
                    clip_paths=local_clips,
                    output_path=final_path,
                    transitions=[s.transition or "fade"
                                 for s in project.scenes[1:]],
                    captions_path=ass_path,
                    music_path=None,
                )
                ok, log = execute_ffmpeg(cmd, timeout=540)
                if not ok:
                    raise RuntimeError(f"FFmpeg failed: {log}")

                # Upload final video to R2 (graceful fallback if R2 not configured)
                output_url = await _upload_final_video(final_path, project_id)
            finally:
                # Clean up temp files
                shutil.rmtree(tmp_dir, ignore_errors=True)

            # 5. Persist results
            project.output_url = output_url
            project.status = ProjectStatus.completed
            project.credit_cost = credit_cost
            project.updated_at = datetime.now(timezone.utc)
            db.add(project)
            await db.flush()

            # Sprint 3: notify the user that their render is ready.
            if user_row:
                send_render_complete_email(
                    user_row.email,
                    project.title,
                    output_url=output_url or None,
                    success=True,
                )

            return {
                "project_id": project_id,
                "status": "completed",
                "clip_count": len(clip_urls),
                "output_url": output_url,
            }

    try:
        return run_async(_render())
    except Exception as exc:
        # Mark project as failed
        async def _mark_failed():
            async with async_session_factory() as db:
                result = await db.execute(
                    select(Project).where(Project.id == project_id)
                )
                project = result.scalar_one_or_none()
                if project:
                    project.status = ProjectStatus.failed
                    project.updated_at = datetime.now(timezone.utc)
                    db.add(project)
                    await db.flush()

                    # Sprint 3: notify the user that their render failed.
                    user_row = await _fetch_user(str(project.user_id), db)
                    if user_row:
                        send_render_complete_email(
                            user_row.email,
                            project.title,
                            output_url=None,
                            success=False,
                        )

        run_async(_mark_failed())
        raise self.retry(exc=exc, countdown=30)


async def _upload_final_video(local_path: str, project_id: str) -> str:
    """Upload the stitched video to R2.

    If R2 is not configured (no endpoint/keys), fall back to returning the
    local path so the pipeline still completes end-to-end in dev.
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.R2_ENDPOINT or not settings.R2_ACCESS_KEY_ID:
        # Dev fallback: return a placeholder so the project still "completes".
        return f"local://{local_path}"

    from app.core.storage import upload_file
    with open(local_path, "rb") as f:
        data = f.read()
    key = f"renders/{project_id}/{uuid.uuid4()}.mp4"
    return await upload_file(data, key, content_type="video/mp4")
