from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.api.router import api_router
from app.core.qdrant import init_collections


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작: DB 테이블 생성 + Qdrant 컬렉션 초기화
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    init_collections()
    yield
    # 종료
    await engine.dispose()


app = FastAPI(
    title="MemeTracker API",
    description="짤과 원작자를 연결하는 검색 엔진",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
