# Sprint 2 — Core Features & Unified API Integration

## Goal
Implement all MVP features, unify external APIs under Kie.ai, and build the full video creation wizard.

## Completed

### Kie.ai Unified API Integration
- [x] Single API key covers: LLM chat, video (Veo/Kling), image (GPT Image 2), TTS (ElevenLabs)
- [x] Removed separate Nous Research key dependency
- [x] Removed separate ElevenLabs key dependency
- [x] `kieai.py` client module with all provider endpoints

### API Routes
- [x] Full auth flow: email signup/login, Google OAuth, JWT verification
- [x] Project CRUD with scene management
- [x] Script generation via LLM (gemini-3-5-flash-openai)
- [x] Avatar CRUD (preset + custom upload)
- [x] Voice listing
- [x] Background listing (static/video)
- [x] Credit balance + transaction tracking
- [x] Stripe checkout/webhook endpoints (prepared, awaiting payment config)

### Frontend
- [x] Login page with Google OAuth + email
- [x] Dashboard with project list + credit widget
- [x] Full 6-step video creation wizard:
  - **Step 1:** Avatar selection
  - **Step 2:** Script writing (manual + AI generate)
  - **Step 3:** Scene configuration (text, duration, transitions)
  - **Step 4:** Voice selection with preview
  - **Step 5:** Background selection
  - **Step 6:** Review & Render
- [x] Project detail page
- [x] Protected routes / auth guard
- [x] Loading skeletons
- [x] Credit balance display

### Rendering Pipeline
- [x] Celery worker with FFmpeg-based video composition
- [x] Scene-by-scene processing with status tracking
- [x] Thumbnail generation for completed renders
- [x] Asynchronous status polling

### Database
- [x] Seed script with 4 avatars, 6 voices, 8 backgrounds
- [x] Automatic table creation on startup

### Deployment
- [x] 5 Docker containers verified running
- [x] Backend health check at /health and /
- [x] Frontend accessible at port 5173
