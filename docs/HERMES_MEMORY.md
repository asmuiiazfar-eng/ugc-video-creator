# Hermes Memory — Project Decisions & Conventions

> Read this before making ANY changes to this project.
> These decisions were made intentionally. Do not reverse them without discussion.

## 🏆 Tech Stack (Locked — Do Not Change)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | **React 18 + Vite 5 + TypeScript** | Fast builds, strict types, no SSR baggage |
| Styling | **Tailwind CSS 3** | Utility-first, no runtime |
| Backend | **FastAPI + Python 3.11** | Async-native, auto-docs, Pydantic |
| ORM | **SQLAlchemy 2.0 (async)** | Mature, async-native, migrations-ready |
| Database | **PostgreSQL 16** | Full-text, JSON, asyncpg support |
| Queue | **Celery 5 + Redis 7** | Industry-standard async task queue |
| Auth | **Supabase** | Built-in Google OAuth + email/password + JWT |
| Storage | **Cloudflare R2** (S3-compatible) | No egress fees, global CDN |
| Payments | **Stripe** | Checkout + webhooks |

## 🔌 External APIs — Kie.ai Only

**All AI features go through Kie.ai with ONE API key.** Do NOT add direct provider integrations.

| Feature | Via | Model |
|---------|-----|-------|
| LLM Chat | Kie.ai `/v1/chat/completions` | `gemini-3-5-flash-openai` |
| Video Gen | Kie.ai `/v1/video/generate` | Veo / Kling |
| Image Gen | Kie.ai `/v1/images/generations` | GPT Image 2 / DALL-E |
| TTS | Kie.ai `/v1/audio/speech` | ElevenLabs |

## 🏗️ Architecture Rules

- **Hot-reload development:** Docker volumes mount local code (backend:/app, frontend:/app)
- **All services** defined in `docker-compose.yml` (postgres, redis, backend, celery-worker, frontend)
- **Env vars** loaded from `.env` via `env_file: .env` in compose, plus `pydantic-settings` in Python
- **Celery broker** is always Redis (already configured)
- **FFmpeg** runs inside the celery-worker container for video composition

## 🗄️ Database Conventions

- All tables use **UUID primary keys** (except backgrounds and voices which use string IDs)
- Timestamps use **UTC**, `DateTime(timezone=True)`
- Soft-deletes are not used (hard delete with cascade)
- Seed data is in `backend/app/seed.py`, run via `docker compose exec backend python -m app.seed`

## 🧪 Development Commands

```bash
# Start everything
docker compose up -d

# Rebuild backend after dependency changes
docker compose build backend && docker compose up -d

# Restart specific service
docker compose restart backend

# View backend logs
docker compose logs -f backend

# Shell into backend container
docker compose exec backend bash

# Run seed script
docker compose exec backend python -m app.seed

# Check backend health
curl http://localhost:8000/health
curl http://localhost:8000/
```

## 📝 Naming Conventions

- **Python:** snake_case files, PascalCase classes, snake_case functions/vars
- **TypeScript:** camelCase vars/functions, PascalCase components/files, kebab-case for folders
- **API routes:** plural nouns (`/projects`, `/avatars`, `/voices`)
- **DB tables:** snake_case, plural (`credit_transactions`, not `credit_transaction`)

## 🚢 Deployment Flow

1. Build images: `docker compose build`
2. Push to registry (future: GitHub Container Registry)
3. Deploy on VPS with Docker Compose
4. Run migrations / seed
5. Configure Supabase production project
6. Set Stripe live keys + webhook endpoint
7. Set R2 credentials

## 🔒 Do Not

- Commit `.env` files (already gitignored)
- Add direct OpenAI / ElevenLabs SDKs (use Kie.ai)
- Switch from PostgreSQL to SQLite
- Add another auth provider
- Remove or rename seed data without updating seed.py
- Change the 6-step wizard flow without planning
