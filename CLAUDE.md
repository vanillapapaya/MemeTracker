# MemeTracker

짤과 원작자를 연결하는 검색 엔진 + 짤 피드 플랫폼.

## Project Overview

- **Search**: Natural language text → image search using hybrid vector search (CLIP visual + e5-large semantic)
- **Feed**: Short-form swipe UI with vector-based recommendations (70% recommended + 30% random)
- **Creator Connection**: Link memes to original creators with profile pages and source tracking

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (Python), Celery/ARQ |
| Frontend | Next.js 14+ (App Router), Tailwind CSS, Swiper.js, Zustand |
| Vector DB | Qdrant (CLIP 512d + e5-large 1024d) |
| RDB | PostgreSQL |
| Cache | Redis |
| Storage | Cloudflare R2 (images), Cloudflare Images (resize) |
| AI/ML | CLIP (ViT-B/32), multilingual-e5-large, Claude Vision (captioning), Falconsai NSFW filter |
| Hosting | Railway (backend), Vercel (frontend), Cloudflare (CDN/domain) |

## Project Structure

```
docs/                         # Design documents (Korean)
  00-프로젝트-개요.md           # Project overview
  01-기술-아키텍처.md           # Technical architecture & DB schema
  02-데이터-파이프라인.md        # Data sources & collection pipeline
  03-API-명세.md               # Backend API spec
  04-프론트엔드-명세.md          # Frontend UI/UX spec
  05-인프라-및-배포.md           # Infrastructure & deployment
  06-법적-체크리스트.md          # Legal checklist (copyright, opt-out)
  07-개발-로드맵.md             # Development roadmap (10 weeks, 7 phases)
  08-토론-요약.md               # Discussion summary
multi_agent_discussion.py     # Multi-agent risk analysis tool (Anthropic API)
discussion_result.md          # Discussion output
```

## Development Phases

- Phase 0: Demand validation (fake door landing page)
- Phase 1: Data collection + infra (seed 1,000 images)
- Phase 2: Search MVP (FastAPI + Next.js)
- Phase 3: Feed MVP (swipe UI + basic recommendations)
- Phase 4: Multi-source expansion (Safebooru, X API, Danbooru)
- Phase 5: Creator system (profiles, OAuth, opt-out)
- Phase 6: Monetization (interstitial ads)

## Conventions

- Documentation language: Korean
- Code comments: Korean or English
- Use Python type hints in backend code
- Follow FastAPI async patterns
- Use Next.js App Router conventions
