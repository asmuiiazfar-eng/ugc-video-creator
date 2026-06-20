# Project Inventory — UGC Video Creator

## Directory Structure

```
/opt/ugc-video-creator/
├── .dockerignore
├── .env                      # Actual secrets (gitignored)
├── .env.example              # Template for local dev
├── .gitignore
├── docker-compose.yml        # All 5 services
├── docs/                     # Project documentation
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── SPRINT_1.md
│   ├── SPRINT_2.md
│   ├── ROADMAP.md
│   ├── PROJECT_INVENTORY.md
│   ├── CODEX_CONTEXT.md
│   ├── HANDOFF_REPORT.md
│   └── HERMES_MEMORY.md
├── backend/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI entrypoint
│       ├── config.py           # Pydantic Settings
│       ├── database.py         # Async engine / session
│       ├── models.py           # SQLAlchemy ORM models
│       ├── seed.py             # DB seed script
│       ├── api/
│       │   ├── __init__.py
│       │   ├── auth.py         # Supabase auth routes
│       │   ├── avatars.py
│       │   ├── backgrounds.py
│       │   ├── credits.py
│       │   ├── projects.py
│       │   ├── scenes.py
│       │   ├── scripts.py      # AI script generation
│       │   └── voices.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── credits.py      # Credit logic
│       │   ├── deps.py         # FastAPI dependencies
│       │   ├── kieai.py        # Unified API client
│       │   ├── render.py       # FFmpeg rendering
│       │   ├── script_gen.py   # LLM prompt templates
│       │   └── storage.py      # R2 storage (prepared)
│       └── workers/
│           ├── __init__.py
│           ├── celery_app.py   # Celery config
│           └── render_tasks.py # Async video rendering
└── frontend/
    ├── .dockerignore
    ├── Dockerfile
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── vite-env.d.ts
        ├── components/
        │   ├── CreditWidget.tsx
        │   ├── Layout.tsx
        │   ├── LoadingSkeleton.tsx
        │   └── ProtectedRoute.tsx
        ├── lib/
        │   ├── api.ts           # Axios HTTP client
        │   ├── supabase.ts      # Supabase client
        │   └── types.ts         # TypeScript types
        ├── pages/
        │   ├── Dashboard.tsx
        │   ├── Login.tsx
        │   └── ProjectDetail.tsx
        └── wizard/
            ├── WizardContainer.tsx
            ├── StepAvatar.tsx
            ├── StepScript.tsx
            ├── StepScenes.tsx
            ├── StepVoice.tsx
            ├── StepBackground.tsx
            └── StepReview.tsx
```

## Major Modules

| Module | Path | Purpose |
|--------|------|---------|
| API Routes | `backend/app/api/` | REST endpoints (FastAPI) |
| Core Logic | `backend/app/core/` | Business logic, AI client, rendering |
| Workers | `backend/app/workers/` | Celery async tasks |
| Frontend Pages | `frontend/src/pages/` | Route-level components |
| Wizard | `frontend/src/wizard/` | 6-step video creation flow |
| Components | `frontend/src/components/` | Reusable UI components |
| Frontend Lib | `frontend/src/lib/` | API client, auth, types |

## APIs (REST)

| Base URL | Description |
|----------|-------------|
| `http://localhost:8000` | Backend API (FastAPI) |
| `http://localhost:5173` | Frontend (Vite dev server) |

## Database Tables (PostgreSQL 16)

| Table | Records (seed) | Purpose |
|-------|---------------|---------|
| `users` | 0 | Auth + credit balance |
| `projects` | 0 | Video projects |
| `scenes` | 0 | Scenes within projects |
| `avatars` | 4 | Preset + custom avatars |
| `backgrounds` | 8 | Static/video backgrounds |
| `voices` | 6 | TTS voice profiles |
| `credit_transactions` | 0 | Credit ledger |

## Integrations

| Service | Type | Status |
|---------|------|--------|
| Kie.ai | LLM + Video + Image + TTS | ✅ Active |
| Supabase | Auth (email + Google OAuth) | ✅ Active |
| PostgreSQL 16 | Database | ✅ Active |
| Redis 7 | Cache + Queue | ✅ Active |
| Cloudflare R2 | Media storage | 🔜 Prepared (needs keys) |
| Stripe | Payments | 🔜 Prepared (needs live keys) |

## Environment Variables (.env)

```
DATABASE_URL          — PostgreSQL connection string
SUPABASE_URL          — Supabase project URL
SUPABASE_ANON_KEY     — Supabase anonymous key
SUPABASE_SERVICE_KEY  — Supabase service role key
REDIS_URL             — Redis connection
CELERY_BROKER_URL     — Celery broker (Redis)
R2_ACCESS_KEY_ID      — Cloudflare R2 (optional)
R2_SECRET_ACCESS_KEY  — Cloudflare R2 (optional)
R2_BUCKET_NAME        — R2 bucket name
R2_ENDPOINT           — R2 endpoint
STRIPE_SECRET_KEY     — Stripe (optional)
STRIPE_WEBHOOK_SECRET — Stripe (optional)
KIEAI_API_KEY         — Unified API key (REQUIRED)
KIEAI_LLM_MODEL       — LLM model slug
KIEAI_TTS_VOICE       — Default TTS voice ID
```

## Third-Party Services

| Service | Purpose | Cost |
|---------|---------|------|
| Supabase (free tier) | Auth + DB (if not self-hosted) | Free |
| Kie.ai | LLM + Video + Image + TTS | Pay-per-use |
| Cloudflare R2 | Media storage (~$0.015/GB) | Minimal |
| Stripe | Payment processing | 2.9% + $0.30 |
| Docker | Containerization | Free |
