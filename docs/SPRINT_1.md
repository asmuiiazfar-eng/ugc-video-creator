# Sprint 1 — Project Foundation

## Goal
Set up the project skeleton: Docker infrastructure, database schema, API scaffolding, and basic frontend.

## Completed

### Infrastructure
- [x] Docker Compose with 5 services (postgres, redis, backend, celery-worker, frontend)
- [x] PostgreSQL 16 with async SQLAlchemy connection
- [x] Redis 7 for Celery broker + cache
- [x] Hot-reload volumes for both backend and frontend
- [x] Health checks on postgres and redis

### Backend
- [x] FastAPI app with lifespan management
- [x] CORS middleware configured
- [x] SQLAlchemy async engine + session factory
- [x] All database models: User, Project, Scene, Avatar, Background, Voice, CreditTransaction
- [x] Pydantic Settings (env-based configuration)
- [x] API stubs for all routes

### Frontend
- [x] Vite + React 18 + TypeScript scaffold
- [x] Tailwind CSS + PostCSS setup
- [x] React Router v6 with basic routes
- [x] Framer Motion integration
- [x] Supabase JS client configured

### Seed Data
- [x] 4 preset avatars
- [x] 6 ElevenLabs voices
- [x] 8 backgrounds across 2 categories
