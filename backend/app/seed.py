"""
Database seed script — presets for avatars, voices, and backgrounds.

Run: python -m app.seed
Needs DATABASE_URL set in .env or env vars.
"""

import asyncio
from sqlalchemy import select, text
from app.database import async_session_factory, engine, Base
from app.models import Avatar, Voice, Background, BackgroundType


PRESET_AVATARS = [
    {
        "source_photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "thumbnail_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200",
        "is_preset": True,
    },
    {
        "source_photo_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "thumbnail_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200",
        "is_preset": True,
    },
    {
        "source_photo_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
        "avatar_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
        "thumbnail_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=200",
        "is_preset": True,
    },
    {
        "source_photo_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "thumbnail_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200",
        "is_preset": True,
    },
]

PRESET_VOICES = [
    # ElevenLabs voices available via Kie.ai
    {
        "id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel",
        "gender": "female",
        "tone": "warm, clear",
        "preview_url": "https://static.aiquickdraw.com/elevenlabs/voice/21m00Tcm4TlvDq8ikWAM.mp3",
        "is_active": True,
    },
    {
        "id": "AZnzlk1XvdvUeBnXmlld",
        "name": "Domi",
        "gender": "female",
        "tone": "calm, soothing",
        "preview_url": "https://static.aiquickdraw.com/elevenlabs/voice/AZnzlk1XvdvUeBnXmlld.mp3",
        "is_active": True,
    },
    {
        "id": "EXAVITQu4vrRV7aRXeB",
        "name": "Bella",
        "gender": "female",
        "tone": "young, expressive",
        "preview_url": "https://static.aiquickdraw.com/elevenlabs/voice/EXAVITQu4vrRV7aRXeB.mp3",
        "is_active": True,
    },
    {
        "id": "ErXwobaYiN019P07SvxV",
        "name": "Antoni",
        "gender": "male",
        "tone": "deep, confident",
        "preview_url": "https://static.aiquickdraw.com/elevenlabs/voice/ErXwobaYiN019P07SvxV.mp3",
        "is_active": True,
    },
    {
        "id": "TxGEqnHWrfWFTfGW9XjX",
        "name": "Josh",
        "gender": "male",
        "tone": "American, friendly",
        "preview_url": "https://static.aiquickdraw.com/elevenlabs/voice/TxGEqnHWrfWFTfGW9XjX.mp3",
        "is_active": True,
    },
    {
        "id": "VR6AewLTigWG4xSOGBG",
        "name": "Arnold",
        "gender": "male",
        "tone": "energetic, narrator",
        "preview_url": "https://static.aiquickdraw.com/elevenlabs/voice/VR6AewLTigWG4xSOGBG.mp3",
        "is_active": True,
    },
]

PRESET_BACKGROUNDS = [
    {
        "id": "bg-modern-office",
        "category": "indoor",
        "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=400",
        "is_video": False,
    },
    {
        "id": "bg-cozy-living-room",
        "category": "indoor",
        "image_url": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
        "is_video": False,
    },
    {
        "id": "bg-sunny-kitchen",
        "category": "indoor",
        "image_url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400",
        "is_video": False,
    },
    {
        "id": "bg-city-rooftop",
        "category": "outdoor",
        "image_url": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=400",
        "is_video": False,
    },
    {
        "id": "bg-cafe-interior",
        "category": "indoor",
        "image_url": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400",
        "is_video": False,
    },
    {
        "id": "bg-nature-park",
        "category": "outdoor",
        "image_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
        "is_video": False,
    },
    {
        "id": "bg-white-studio",
        "category": "studio",
        "image_url": "https://images.unsplash.com/photo-1598387993281-cecf8b71a8f8?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1598387993281-cecf8b71a8f8?w=400",
        "is_video": False,
    },
    {
        "id": "bg-product-shelf",
        "category": "studio",
        "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=1280",
        "thumbnail_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400",
        "is_video": False,
    },
]


async def seed():
    print("⏳ Creating tables if needed...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Check if seed already done
        result = await db.execute(select(Avatar).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  Seed data already exists. Skipping.")
            return

        print("🌱 Seeding presets...")

        # Avatars
        for av in PRESET_AVATARS:
            db.add(Avatar(**av))
        print(f"  ✓ {len(PRESET_AVATARS)} avatars")

        # Voices
        for vc in PRESET_VOICES:
            db.add(Voice(**vc))
        print(f"  ✓ {len(PRESET_VOICES)} voices")

        # Backgrounds
        for bg in PRESET_BACKGROUNDS:
            db.add(Background(**bg))
        print(f"  ✓ {len(PRESET_BACKGROUNDS)} backgrounds")

        await db.commit()
        print("✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
