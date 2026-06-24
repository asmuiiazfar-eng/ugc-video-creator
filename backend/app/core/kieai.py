"""
Unified Kie.ai API client.

Covers:
  - Chat completions (OpenAI-compatible) — sync
  - Video generation (Veo/Kling) — async task + poll
  - Image generation (GPT Image 2, etc.) — async task + poll
  - TTS (ElevenLabs via Kie.ai) — async task + poll

Single API key covers everything.
"""

import asyncio
import json
import httpx
from typing import Optional

from app.config import get_settings

settings = get_settings()

KIEAI_BASE = settings.KIEAI_BASE_URL.rstrip("/")

# ── Internal helpers ──────────────────────────────────────────────────


async def _request(method: str, url: str, json_data: Optional[dict] = None,
                   timeout: int = 120) -> dict:
    """Make a raw HTTP request to Kie.ai with 3× retry + exponential backoff."""
    headers = {
        "Authorization": f"Bearer {settings.KIEAI_API_KEY}",
        "Content-Type": "application/json",
    }
    last_exception = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    resp = await client.get(url, headers=headers)
                else:
                    resp = await client.post(url, headers=headers, json=json_data)

                if resp.status_code == 429:
                    await asyncio.sleep((2 ** attempt) * 2)
                    continue
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            last_exception = e
            if attempt < 2:
                await asyncio.sleep((2 ** attempt) * 2)
            continue
    raise Exception(f"Kie.ai request failed after 3 retries — {last_exception}")


async def _poll_task(task_id: str, detail_endpoint: str,
                     timeout: int = 300, interval: float = 3.0) -> dict:
    """Poll an async task until completion, failure, or timeout."""
    url = f"{KIEAI_BASE}{detail_endpoint}?taskId={task_id}"
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        data = await _request("GET", url, timeout=30)
        code = data.get("code", 0)
        state = ""
        if data.get("data"):
            state = (data["data"].get("state") or
                     data["data"].get("status") or "")
        if code == 200 and state in ("success", "completed", "succeed"):
            return data
        if code != 200 or state in ("fail", "failed", "error"):
            msg = (data.get("msg") or
                   data.get("data", {}).get("failMsg") or
                   data.get("data", {}).get("error_message") or
                   "Unknown error")
            raise Exception(f"Task {task_id} failed: {msg}")
        await asyncio.sleep(interval)
    raise TimeoutError(f"Task {task_id} timed out after {timeout}s")


# ── 1. Chat Completions (OpenAI-compatible, sync) ─────────────────────


async def chat_completion(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: Optional[dict] = None,
) -> dict:
    """Send a chat completion request via Kie.ai's OpenAI-compatible endpoint.

    Endpoint: POST https://api.kie.ai/{MODEL_SLUG}/v1/chat/completions
    Model slugs: gemini-3-5-flash-openai, claude-sonnet-4-6, deepseek-v4-flash, etc.
    """
    slug = model or settings.KIEAI_LLM_MODEL
    url = f"{KIEAI_BASE}/{slug}/v1/chat/completions"
    payload = {
        "model": slug,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format
    return await _request("POST", url, payload, timeout=120)


# ── 2. Video Generation (Veo / Kling) ────────────────────────────────


async def generate_video(
    prompt: str,
    model: str = "veo3_fast",
    aspect_ratio: str = "9:16",
    image_url: Optional[str] = None,
    call_back_url: Optional[str] = None,
) -> dict:
    """Generate a video via Kie.ai Veo API (async task).

    POST /api/v1/veo/generate → returns {code: 200, data: {taskId: ...}}
    Poll with GET /api/v1/veo/record-detail?taskId=...
    """
    url = f"{KIEAI_BASE}/api/v1/veo/generate"
    payload = {
        "prompt": prompt,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "enableTranslation": True,
        "watermark": "",
    }
    if image_url:
        payload["imageUrls"] = [image_url]
        payload["generationType"] = "FIRST_AND_LAST_FRAMES_2_VIDEO"
    if call_back_url:
        payload["callBackUrl"] = call_back_url
    return await _request("POST", url, payload, timeout=60)


async def poll_video(task_id: str, timeout: int = 300) -> dict:
    """Poll a video generation task until complete."""
    return await _poll_task(task_id, "/api/v1/veo/record-detail", timeout=timeout)


# ── 3. Image Generation (General jobs — GPT Image 2, etc.) ────────────


async def generate_image(
    prompt: str,
    model: str = "gpt-image-2",
    aspect_ratio: str = "16:9",
    call_back_url: Optional[str] = None,
) -> dict:
    """Generate an image via Kie.ai general job API (async task).

    POST /api/v1/jobs/createTask → returns {code: 200, data: {taskId: ...}}
    Poll with GET /api/v1/common/get-task-detail?taskId=...
    """
    url = f"{KIEAI_BASE}/api/v1/jobs/createTask"
    payload = {
        "model": model,
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        },
    }
    if call_back_url:
        payload["callBackUrl"] = call_back_url
    return await _request("POST", url, payload, timeout=60)


async def poll_job(task_id: str, timeout: int = 120) -> dict:
    """Poll a general job task (image, TTS, etc.) until complete."""
    return await _poll_task(task_id, "/api/v1/common/get-task-detail", timeout=timeout)


# ── 4. Text-to-Speech (ElevenLabs via Kie.ai) ─────────────────────────


async def text_to_speech(
    text: str,
    voice_id: Optional[str] = None,
    model: str = "elevenlabs/text-to-speech-multilingual-v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    call_back_url: Optional[str] = None,
) -> str:
    """Convert text to speech via Kie.ai ElevenLabs integration.

    Returns the audio URL after polling for completion.

    POST /api/v1/jobs/createTask with model="elevenlabs/..."
    Poll with GET /api/v1/common/get-task-detail?taskId=...
    """
    url = f"{KIEAI_BASE}/api/v1/jobs/createTask"
    payload = {
        "model": model,
        "input": {
            "text": text,
            "voice": voice_id or settings.KIEAI_TTS_VOICE,
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": 0,
            "speed": 1,
        },
    }
    if call_back_url:
        payload["callBackUrl"] = call_back_url

    # Create task
    result = await _request("POST", url, payload, timeout=30)
    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        raise Exception(f"TTS task creation failed: {result.get('msg', 'no taskId')}")

    # Poll for completion
    poll_result = await poll_job(task_id, timeout=120)
    data = poll_result.get("data", {})

    # Extract audio URL from poll response
    audio_url = (
        data.get("audio_url") or
        data.get("resultUrls", [None])[0] or
        data.get("url")
    )
    if not audio_url:
        raise Exception(f"TTS completed but no audio URL in response: {data}")
    return audio_url


# ── 5. Avatar Generation ──────────────────────────────────────────────


async def generate_avatar(source_image_url: str) -> dict:
    """Generate an avatar from a source photo using Kie.ai.

    Delegates to the Veo API internally for avatar generation.
    Returns the avatar URL and thumbnail.
    """
    # For now, use GPT Image 2 via general job API to process avatar
    # In production, swap to a dedicated avatar model
    url = f"{KIEAI_BASE}/api/v1/jobs/createTask"
    payload = {
        "model": "gpt-image-2",
        "input": {
            "prompt": f"Generate a professional avatar photo based on this reference image: {source_image_url}",
            "aspect_ratio": "1:1",
        },
    }
    result = await _request("POST", url, payload, timeout=60)
    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        raise Exception(f"Avatar task creation failed: {result.get('msg', 'no taskId')}")
    poll_result = await poll_job(task_id, timeout=120)
    data = poll_result.get("data", {})
    avatar_url = (
        data.get("resultUrls", [None])[0] or
        data.get("url") or
        ""
    )
    return {
        "avatar_url": avatar_url,
        "thumbnail_url": avatar_url,
    }


async def generate_background(prompt: str) -> dict:
    """Generate a background image from a text prompt using Kie.ai.

    Uses GPT Image 2 via general job API.
    """
    url = f"{KIEAI_BASE}/api/v1/jobs/createTask"
    payload = {
        "model": "gpt-image-2",
        "input": {
            "prompt": prompt,
            "aspect_ratio": "16:9",
        },
    }
    result = await _request("POST", url, payload, timeout=60)
    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        raise Exception(f"Background task failed: {result.get('msg', 'no taskId')}")
    poll_result = await poll_job(task_id, timeout=120)
    data = poll_result.get("data", {})
    image_url = (
        data.get("resultUrls", [None])[0] or
        data.get("url") or
        ""
    )
    return {"image_url": image_url, "thumbnail_url": image_url}


# ── 7. Legacy / Scene generation (compat) ──────────────────────────────


async def generate_scene(
    avatar_url: str,
    audio_url: str,
    background_url: str,
    scene_text: Optional[str] = None,
) -> dict:
    """Generate a video scene with avatar, audio, and background.

    Issue 5 fix: Veo expects a NATURAL LANGUAGE prompt — it cannot interpret
    raw URLs embedded in the prompt text. The avatar is now passed via the
    `imageUrls` parameter (first-and-last-frames-to-video mode), and the prompt
    describes the desired scene in plain language derived from the scene text.
    """
    # Build a descriptive, natural-language prompt. Prefer the scene's actual
    # script text (which is already meaningful) and layer on staging cues.
    if scene_text:
        spoken = scene_text.strip()
        prompt = (
            f"A friendly content creator speaks directly to camera, delivering "
            f"this line with natural energy and clear lip movements: \"{spoken}\". "
            f"Natural studio lighting, steady medium close-up framing, "
            f"professional UGC advertisement style."
        )
    else:
        prompt = (
            "A person speaking naturally and confidently to camera in a "
            "professional UGC advertisement style. Natural lip movements, "
            "steady medium close-up framing, soft studio lighting."
        )

    # The avatar image drives the on-camera person via image-to-video mode.
    # Only pass a real URL — never a UUID or DB id.
    image_input = avatar_url if avatar_url.startswith("http") else None

    result = await generate_video(prompt=prompt, image_url=image_input)
    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        raise Exception(f"Scene generation failed: {result.get('msg', 'no taskId')}")
    poll_result = await poll_video(task_id, timeout=300)
    data = poll_result.get("data", {})

    video_url = (
        data.get("videoInfo", {}).get("resultUrls", [None])[0]
        or data.get("videoInfo", {}).get("videoUrl")
    )
    return {"video_url": video_url or "", "task_id": task_id}


# ── 6. Utilities ──────────────────────────────────────────────────────


async def check_balance() -> dict:
    """Check Kie.ai credit balance.

    GET /api/v1/chat/credit
    """
    url = f"{KIEAI_BASE}/api/v1/chat/credit"
    return await _request("GET", url, timeout=15)
