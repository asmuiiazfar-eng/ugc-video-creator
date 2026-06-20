# Product Requirements Document — UGC Video Creator

## 1. Product Purpose

A web application that allows businesses (especially YouTube Ads specialists) to create **AI-generated UGC-style video ads** at scale. Users select a digital avatar, write a script, pick a background, choose a voice, and render a complete talking-head video — no filming, no actors, no studio.

## 2. Target Users

- YouTube Ads / Google Ads specialists
- Social media content managers
- E-commerce brands running video ads
- Small businesses without video production capability

## 3. Core Features

| Feature | Status |
|---------|--------|
| Avatar selection (preset + custom from photo) | ✅ Sprint 2 |
| AI script generation (LLM via Kie.ai) | ✅ Sprint 2 |
| Voice selection (ElevenLabs TTS via Kie.ai) | ✅ Sprint 2 |
| Scene-by-scene video composition | ✅ Sprint 2 |
| Background selection (static/video/AI) | ✅ Sprint 2 |
| Background removal (avatar cutout) | ✅ Sprint 2 |
| Credit-based billing system | ✅ Sprint 2 |
| Supabase Auth (Google OAuth + email) | ✅ Sprint 2 |
| Video rendering pipeline (Celery + FFmpeg) | ✅ Sprint 2 |
| Thumbnail generation | ✅ Sprint 2 |

## 4. Future Features (Sprint 3+)

- Stripe payment integration (top-up credits)
- Cloudflare R2 storage for rendered videos
- Multi-language TTS
- Batch video generation
- Template library
- Analytics dashboard (CTR, impressions)
- Team/collaboration accounts

## 5. Success Metrics

- Video render time < 5 minutes
- Cost per video < $0.50
- User can go from login → rendered video in < 10 clicks
- Support 1080p output
