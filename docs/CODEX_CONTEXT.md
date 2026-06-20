# Codex Context — UGC Video Creator

## Project Summary

A web application for creating AI-generated **UGC (User-Generated Content) style video ads** at scale. Users select avatars, write scripts, pick voices and backgrounds, and render talking-head videos — no filming required. Built for YouTube Ads / social media specialists.

**Current Implementation Status:** Sprint 2 Completed (MVP-ready)

### Completed Features
- Docker Compose infrastructure (Postgres, Redis, Backend, Celery, Frontend)
- Full REST API (FastAPI) with auth, projects, scenes, avatars, voices, backgrounds, scripts, credits
- Vue-style video creation wizard (6 steps)
- AI script generation via Kie.ai LLM
- Celery-based video rendering pipeline with FFmpeg
- Supabase Auth (email + Google OAuth)
- Credit-based billing system
- Seed data (4 avatars, 6 voices, 8 backgrounds)

### Pending Features
- Stripe payment integration (endpoints prepared, needs live keys)
- Cloudflare R2 storage activation (prepared, needs keys + credentials)
- Multi-language TTS
- Batch video generation
- Template library
- Analytics dashboard

## Architecture

### Frontend Stack (Vite + React + TypeScript)
```
frontend/
├── src/
│   ├── pages/           # Route-level pages (Login, Dashboard, ProjectDetail)
│   ├── wizard/          # 6-step video creation wizard
│   │   ├── WizardContainer.tsx
│   │   ├── StepAvatar.tsx
│   │   ├── StepScript.tsx
│   │   ├── StepScenes.tsx
│   │   ├── StepVoice.tsx
│   │   ├── StepBackground.tsx
│   │   └── StepReview.tsx
│   ├── components/      # Reusable UI (Layout, CreditWidget, ProtectedRoute)
│   ├── lib/             # API client (axios), Supabase client, types
│   └── App.tsx          # Routes
```

### Backend Stack (FastAPI + SQLAlchemy Async + Celery)
```
backend/
├── app/
│   ├── api/             # REST routes (auth, projects, scenes, avatars, etc.)
│   ├── core/            # Business logic
│   │   ├── kieai.py     # Unified API client (LLM, Video, Image, TTS)
│   │   ├── render.py    # FFmpeg video composition
│   │   ├── script_gen.py # LLM prompt templates
│   │   ├── credits.py   # Credit logic
│   │   ├── storage.py   # Cloudflare R2 (prepared)
│   │   └── deps.py      # FastAPI dependencies
│   ├── workers/         # Celery async tasks
│   │   ├── celery_app.py
│   │   └── render_tasks.py
│   ├── models.py        # SQLAlchemy ORM (7 tables)
│   ├── config.py        # Pydantic Settings
│   └── seed.py          # DB seed script
```

### Database (PostgreSQL 16)
Tables: users, projects, scenes, avatars, backgrounds, voices, credit_transactions

### Storage
- Cloudflare R2 (S3-compatible) — **prepared but not active**
- Media files: rendered videos, thumbnails, avatar photos

### Authentication
- Supabase Auth (email/password + Google OAuth)
- JWT verification via `python-jose`
- Protected routes with FastAPI dependency injection

### External APIs (via Kie.ai — Unified Key)
| Service | What it does | Model |
|---------|-------------|-------|
| LLM | Script generation | gemini-3-5-flash-openai |
| Video | Scene video generation | Veo / Kling |
| Image | Backgrounds & thumbnails | GPT Image 2 / DALL-E |
| TTS | Voiceover | ElevenLabs |

## Sprint Progress

### ✅ Sprint 1 — Foundation
Docker infra, DB schema, FastAPI scaffolding, Vite/React scaffold, seed data.

### ✅ Sprint 2 — Core Features
Kie.ai integration, auth, wizard, Celery rendering, credit system, preset content.

### 🔜 Sprint 3 — Payments & Storage
Stripe live keys, R2 storage, email notifications, credit purchase flow.

## Development Rules

### Coding Standards
- **Python:** PEP 8, async/await for I/O, type hints required
- **TypeScript:** Strict mode, explicit types, no `any`
- **React:** Functional components + hooks, no class components
- **CSS:** Tailwind utility classes, no separate CSS files unless necessary

### Folder Conventions
- Backend routes in `api/` — one file per resource
- Frontend pages in `pages/`, multi-step flows in dedicated folders
- Shared logic in `lib/`
- Documentation in `docs/`

### Naming Conventions
- **Python files:** snake_case
- **TypeScript files:** PascalCase for components, camelCase for utilities
- **API routes:** RESTful plural names (`/projects`, `/avatars`)
- **DB tables:** snake_case, plural

### Deployment Process
```bash
# Development
docker compose up -d

# Backend only (reload)
docker compose restart backend

# View logs
docker compose logs -f backend

# Seed database
docker compose exec backend python -m app.seed
```

## Important Decisions (Do NOT Change)

- **Kie.ai is the ONLY external AI provider** — do not add OpenAI direct, ElevenLabs direct, or any other AI API. All LLM, video, image, and TTS go through Kie.ai.
- **Supabase is the ONLY auth provider** — do not add Auth0, Clerk, or Firebase Auth.
- **PostgreSQL 16 is the DB** — do not switch to SQLite, MySQL, or MongoDB.
- **Cloudflare R2 is the media storage** — do not add S3 or Wasabi.
- **Stripe is the payment processor** — do not add Paddle, Lemon Squeezy, or PayPal.
- **React + Vite is the frontend** — do not switch to Next.js, Remix, or Svelte.
- **FastAPI is the backend** — do not switch to Django, Flask, or Express.

## Quick Start (Local)

1. Copy `.env.example` → `.env` and fill in values
2. `docker compose up -d`
3. Backend at http://localhost:8000
4. Frontend at http://localhost:5173
5. Seed: `docker compose exec backend python -m app.seed`
