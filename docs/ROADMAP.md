# Product Roadmap

## ✅ Sprint 1 — Foundation
- [x] Docker Compose infra (Postgres, Redis, Backend, Celery, Frontend)
- [x] Database schema (all 7 tables)
- [x] FastAPI scaffolding + SQLAlchemy async
- [x] Vite + React + Tailwind scaffold
- [x] Seed data (avatars, voices, backgrounds)

## ✅ Sprint 2 — Core Features
- [x] Kie.ai unified API integration (LLM, Video, Image, TTS)
- [x] Full auth flow (email + Google OAuth)
- [x] Project CRUD + scene management
- [x] AI script generation
- [x] 6-step video creation wizard
- [x] Celery rendering pipeline + FFmpeg
- [x] Credit system (balance + transactions)
- [x] Preset avatars, voices, backgrounds

## 🔜 Sprint 3 — Payments & Storage
- [x] Stripe checkout session (prepared, needs live keys)
- [x] Stripe webhook (prepared, needs endpoint)
- [ ] Activate Cloudflare R2 storage for video uploads
- [ ] Stripe production keys + webhook configuration
- [ ] Credit purchase flow end-to-end
- [ ] Email notifications on render complete

## 🔜 Sprint 4 — Quality & Scale
- [ ] Multi-language TTS support
- [ ] Batch video generation (multi-project at once)
- [ ] Video template library
- [ ] Custom branding overlays
- [ ] Watermark options
- [ ] Render quality settings (720p / 1080p / 4K)

## 🔜 Sprint 5 — Analytics & Dashboard
- [ ] Video performance metrics (views, CTR)
- [ ] A/B testing for video variants
- [ ] Usage analytics per user
- [ ] Admin dashboard
- [ ] Team/collaboration accounts
- [ ] API usage billing reports

## 🔮 Future Considerations
- Mobile app (React Native)
- Real-time collaboration
- AI-powered A/B testing recommendations
- Direct YouTube Ads API integration
- White-label solution
