import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_factory
from app.models import Project, Scene, ProjectStatus, SceneRenderStatus
from app.core.kieai import generate_scene as kieai_generate_scene
from app.core.render import stitch_clips, generate_ass_captions
from app.core.storage import upload_file
from app.core.kieai import text_to_speech
from app.core.credits import deduct_credits


def run_async(coro):
    """Run an async coroutine in a sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=2)
def render_project(self, project_id: str):
    """Celery task to render a full project.

    Fetches the project and all scenes, dispatches parallel Kie.ai renders
    (TTS → scene generation), then FFmpeg stitch.
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

            # Process each scene: TTS → Kie.ai render
            clip_urls = []
            captions_data = []

            for scene in project.scenes:
                try:
                    # Mark scene as rendering
                    scene.render_status = SceneRenderStatus.rendering
                    db.add(scene)
                    await db.flush()

                    # 1. Generate TTS audio
                    voice_id = project.voice_id or "21m00Tcm4TlvDq8ikWAM"
                    audio_url = await text_to_speech(scene.text, voice_id)

                    # 2. Generate video scene via Kie.ai
                    avatar_id_str = str(project.avatar_id) if project.avatar_id else ""
                    bg_url = scene.background_id or ""

                    render_result = await kieai_generate_scene(
                        avatar_url=avatar_id_str,
                        audio_url=audio_url,
                        background_url=bg_url,
                    )

                    scene_url = render_result.get("video_url", render_result.get("url", ""))
                    clip_urls.append(scene_url)
                    captions_data.append({
                        "text": scene.text,
                        "estimated_duration": scene.estimated_duration or 8.0,
                    })

                    scene.render_status = SceneRenderStatus.completed
                    scene.render_url = scene_url
                    db.add(scene)
                    await db.flush()

                except Exception as e:
                    scene.render_status = SceneRenderStatus.failed
                    db.add(scene)
                    await db.flush()
                    raise

            # 3. Generate captions
            ass_content = generate_ass_captions(captions_data)

            # 4. Build FFmpeg stitch command
            ffmpeg_cmd = stitch_clips(
                clip_urls=clip_urls,
                transitions=[s.transition or "fade" for s in project.scenes[1:]],
                captions_text="captions.ass",
                music_url=None,
            )

            # Save the command for execution
            project.output_url = ffmpeg_cmd
            project.status = ProjectStatus.completed
            project.credit_cost = credit_cost
            db.add(project)
            await db.flush()

            return {
                "project_id": project_id,
                "status": "completed",
                "clip_count": len(clip_urls),
                "ffmpeg_command": ffmpeg_cmd,
                "ass_captions": ass_content,
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
                    db.add(project)
                    await db.flush()

        run_async(_mark_failed())
        raise self.retry(exc=exc, countdown=30)