"""FFmpeg helpers: command building, execution, and clip downloading.

Issue 2 fix: Previously these functions only *built* command strings without
executing them. They now (a) build a correct filter_complex chain, (b) actually
run FFmpeg via subprocess, and (c) download remote clips to local temp files
first (FFmpeg cannot fetch arbitrary HTTPS URLs reliably through filter_complex).
"""

import os
import shutil
import subprocess
import tempfile
from typing import Optional
from urllib.parse import urlparse

import httpx


def download_clip(url: str, dest_path: str, timeout: int = 120) -> str:
    """Download a remote video/audio clip to a local path (sync).

    FFmpeg's filter_complex cannot reliably ingest arbitrary HTTPS URLs, so we
    stage clips locally first. Returns the local path on success.
    """
    headers = {"User-Agent": "ugc-video-creator/1.0"}
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        with client.stream("GET", url, headers=headers) as resp:
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
    return dest_path


def stitch_clips(
    clip_paths: list[str],
    output_path: str,
    transitions: Optional[list[str]] = None,
    captions_path: Optional[str] = None,
    music_path: Optional[str] = None,
) -> str:
    """Build a CORRECT FFmpeg command to stitch local video clips.

    Issue 2 fix: the previous implementation appended two separate
    `-filter_complex` flags when both captions and music were supplied, which
    produced an invalid command. Captions + music are now merged into a single
    filter chain.

    All inputs must be local file paths (use download_clip first).
    Returns the FFmpeg command as a list of arguments.
    """
    if not clip_paths:
        return []

    if transitions is None:
        transitions = ["fade"] * max(0, len(clip_paths) - 1)

    filter_parts = []

    # Normalize every input: reset timestamps so concat lines up.
    for i in range(len(clip_paths)):
        v_label = f"v{i}"
        a_label = f"a{i}"
        # If a clip has no audio stream, fall back to anullsrc later; for now
        # assume each scene clip carries audio from TTS.
        filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps=30,format=yuv420p[{v_label}]")
        filter_parts.append(f"[{i}:a]aresample=44100[{a_label}]")

    v_labels = "".join(f"[v{i}]" for i in range(len(clip_paths)))
    a_labels = "".join(f"[a{i}]" for i in range(len(clip_paths)))
    filter_parts.append(
        f"{v_labels}{a_labels}concat=n={len(clip_paths)}:v=1:a=1[concat_v][concat_a]"
    )

    # Subtitles (ASS) overlay on the concatenated video.
    out_video_label = "[concat_v]"
    if captions_path:
        # Escape backslashes/colons for the subtitles filter on Windows paths.
        esc = captions_path.replace("\\", "/").replace(":", r"\:")
        filter_parts.append(
            f"[concat_v]subtitles='{esc}'[captioned_v]"
        )
        out_video_label = "[captioned_v]"

    # Mix in background music (local file) if provided.
    if music_path:
        music_idx = len(clip_paths)  # music is the next -i input
        filter_parts.append(
            f"[{music_idx}:a]volume=0.15[bgm];"
            f"[concat_a]amix=inputs=1[mixed_a];"
            f"[mixed_a][bgm]amix=inputs=2:duration=first:dropout_transition=0[final_a]"
        )
        out_audio_label = "[final_a]"
    else:
        out_audio_label = "[concat_a]"

    filter_complex = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"]
    for path in clip_paths:
        cmd += ["-i", path]
    if music_path:
        cmd += ["-i", music_path]
    cmd += [
        "-filter_complex", filter_complex,
        "-map", out_video_label,
        "-map", out_audio_label,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    return cmd


def execute_ffmpeg(cmd: list[str], timeout: int = 540) -> tuple[bool, str]:
    """Run an FFmpeg command via subprocess.

    Issue 2 fix: previously the render pipeline only built the command string
    and stored it; nothing was ever executed. Returns (success, combined_output).
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return False, proc.stderr or proc.stdout or "FFmpeg failed with no output"
        return True, proc.stdout
    except subprocess.TimeoutExpired:
        return False, f"FFmpeg timed out after {timeout}s"
    except FileNotFoundError:
        return False, "ffmpeg binary not found on PATH"
    except Exception as e:
        return False, str(e)


def generate_ass_captions(scenes: list[dict]) -> str:
    """Generate ASS subtitle content from scene data.

    Each scene dict should have 'text' and optionally 'estimated_duration'.
    Returns the complete ASS file content as a string.
    """
    lines = [
        "[Script Info]",
        "; Generated by UGC Video Creator",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,40,1",
        "Style: Caption,Arial,36,&H00FFFFFF,&H000000FF,&H80000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,8,10,10,80,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    current_time = 0.0
    for scene in scenes:
        duration = float(scene.get("estimated_duration", 8.0) or 8.0)
        text = scene.get("text", "")

        start_h = int(current_time // 3600)
        start_m = int((current_time % 3600) // 60)
        start_s = current_time % 60
        end_time = current_time + duration
        end_h = int(end_time // 3600)
        end_m = int((end_time % 3600) // 60)
        end_s = end_time % 60

        start_str = f"{start_h:01d}:{start_m:02d}:{start_s:05.2f}"
        end_str = f"{end_h:01d}:{end_m:02d}:{end_s:05.2f}"

        # Escape ASS special characters
        safe_text = text.replace("{", "\\{").replace("}", "\\}")
        safe_text = safe_text.replace("\n", "\\N")

        lines.append(
            f"Dialogue: 0,{start_str},{end_str},Caption,,0,0,0,,{safe_text}"
        )
        current_time = end_time

    return "\n".join(lines)
