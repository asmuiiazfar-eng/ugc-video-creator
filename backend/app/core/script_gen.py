import json
from typing import Optional

from app.core.kieai import chat_completion

# System prompt for script generation
SYSTEM_PROMPT = """You are an expert UGC (User Generated Content) video script writer. 
Your task is to write compelling, conversational video scripts for product promotions.
Each script should be divided into scenes with clear timing and visual descriptions.
Return ONLY valid JSON with this exact structure:
{
  "scenes": [
    {
      "scene_number": 1,
      "text": "The narration text for this scene",
      "estimated_duration": 8.0,
      "background_prompt": "Description of the background to generate",
      "transition": "fade"
    }
  ],
  "total_duration": 60.0,
  "hook": "Opening line",
  "cta": "Call to action"
}

Rules:
- Each scene should be 5-15 seconds long
- Total script should match the requested duration
- Use natural, conversational language
- Include visual descriptions in background_prompt
- Keep transitions simple: fade, cut, dissolve, slide"""


async def generate_script(
    product_name: str,
    description: str,
    audience: str,
    tone: str,
    duration: int = 60,
) -> dict:
    """Generate a video script using Kie.ai LLM (OpenAI-compatible endpoint)."""
    user_prompt = f"""Create a {duration}-second UGC video script for:

Product: {product_name}
Description: {description}
Target Audience: {audience}
Tone: {tone}

Return the script as JSON with scenes, timings, and visual descriptions."""

    result = await chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    content = result["choices"][0]["message"]["content"]

    # Parse the JSON response
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise ValueError(f"Failed to parse script JSON: {content[:500]}")


async def split_script(script_text: str) -> dict:
    """Parse a raw script text into structured scenes using Kie.ai LLM."""
    result = await chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Split this script into scenes. Return JSON with scenes array:\n\n{script_text}"},
        ],
        temperature=0.3,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    content = result["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise ValueError(f"Failed to parse split script: {content[:500]}")
