# Architecture — UGC Video Creator

## System Overview

```
Frontend (Vite + React + Tailwind)
        │
        ▼ HTTP (REST API)
Backend (FastAPI + SQLAlchemy Async)
        │
        ├──► PostgreSQL 16
        ├──► Redis (Celery broker + cache)
        └──► Celery Workers (video rendering)
                │
                └──► Kie.ai API (LLM / Video / Image / TTS)
```

## Services (Docker Compose)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `postgres` | postgres:16-alpine | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | Celery broker + cache |
| `backend` | Custom (./backend) | 8000 | FastAPI REST API |
| `celery-worker` | Custom (./backend) | — | Async video rendering |
| `frontend` | Custom (./frontend) | 5173 | React + Vite SPA |

## Frontend Stack

- **Framework:** React 18 + TypeScript
- **Build:** Vite 5
- **Routing:** react-router-dom v6
- **State/HTTP:** axios
- **Styling:** Tailwind CSS 3 + autoprefixer
- **Animations:** Framer Motion
- **Auth:** Supabase JS Client
- **Icons:** Lucide React

## Backend Stack

- **Framework:** FastAPI 0.115
- **ORM:** SQLAlchemy 2.0 (async with asyncpg)
- **Task Queue:** Celery 5.4 + Redis
- **Validation:** Pydantic Settings
- **Auth:** Supabase (JWT verification via python-jose)
- **Media:** Cloudflare R2 (boto3) — prepared, not wired
- **Payments:** Stripe — prepared, not wired

## External APIs (via Kie.ai)

| Service | Purpose | Kie.ai Endpoint |
|---------|---------|-----------------|
| LLM (Gemini 3.5 Flash) | Script generation | `/v1/chat/completions` |
| Video (Veo / Kling) | Scene video generation | `/v1/video/generate` |
| Image (GPT Image 2 / DALL-E) | Background images / thumbnails | `/v1/images/generations` |
| TTS (ElevenLabs) | Voiceover generation | `/v1/audio/speech` |

## Database Schema

```
users
├── id (UUID, PK)
├── email (unique)
├── credits (int)
├── plan (enum: free/pro/enterprise)
└── created_at

projects
├── id (UUID, PK)
├── user_id (FK → users)
├── title
├── status (enum: draft/rendering/completed/failed)
├── avatar_id (FK → avatars)
├── voice_id
├── duration_seconds
├── thumbnail_url
├── output_url
├── credit_cost
└── timestamps

scenes
├── id (UUID, PK)
├── project_id (FK → projects)
├── scene_number
├── text
├── estimated_duration
├── background_id
├── background_type (enum: static/video/ai_generated)
├── transition
├── render_status (enum: pending/rendering/completed/failed)
├── render_url
└── timestamps

avatars
├── id (UUID, PK)
├── user_id (FK → users, nullable)
├── source_photo_url
├── avatar_url
├── thumbnail_url
├── is_preset (bool)
└── created_at

backgrounds
├── id (string, PK)
├── category
├── image_url
├── thumbnail_url
└── is_video (bool)

voices
├── id (string, PK)
├── name
├── gender
├── tone
├── audio_url
├── preview_url
└── is_active (bool)

credit_transactions
├── id (UUID, PK)
├── user_id (FK → users)
├── amount
├── action (purchase/usage/refund/bonus)
├── reference_id
└── created_at
```

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/signup` | Email registration |
| POST | `/auth/login` | Email login |
| GET | `/auth/me` | Current user profile |
| POST | `/auth/google` | Google OAuth token exchange |
| GET | `/projects` | List user's projects |
| POST | `/projects` | Create project |
| GET | `/projects/{id}` | Get project detail |
| PATCH | `/projects/{id}` | Update project |
| POST | `/projects/{id}/scenes` | Add scene |
| PATCH | `/projects/{id}/scenes/{scene_id}` | Update scene |
| DELETE | `/projects/{id}/scenes/{scene_id}` | Delete scene |
| POST | `/projects/{id}/render` | Start rendering |
| GET | `/projects/{id}/status` | Render status |
| GET | `/scripts/generate` | AI script generation |
| GET | `/avatars` | List avatars (preset + user's) |
| POST | `/avatars` | Create custom avatar |
| GET | `/voices` | List voices |
| GET | `/backgrounds` | List backgrounds |
| GET | `/credits/balance` | User credit balance |
| POST | `/credits/create-checkout-session` | Stripe checkout (prepared) |
| POST | `/credits/webhook` | Stripe webhook (prepared) |
