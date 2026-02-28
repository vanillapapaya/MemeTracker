from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.image import Image
from app.schemas.image import ImageResponse, SearchResponse, CreatorResponse
from app.services.vector_search import hybrid_search
from app.core.r2 import get_thumbnail_url

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="검색 쿼리"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    type: str = Query("all", description="콘텐츠 타입: meme, illustration, all"),
    source: str = Query("all", description="소스: twitter, safebooru, manual, all"),
    db: AsyncSession = Depends(get_db),
):
    """자연어 텍스트로 이미지 검색 (하이브리드 벡터 검색)"""
    # 벡터 검색
    vector_results = hybrid_search(q, limit=limit, offset=offset, content_type=type, source=source)

    if not vector_results:
        return SearchResponse(results=[], total=0, has_more=False)

    # DB에서 이미지 메타데이터 조회
    image_ids = [r["image_id"] for r in vector_results]
    stmt = select(Image).where(Image.id.in_(image_ids)).options(selectinload(Image.creator))
    result = await db.execute(stmt)
    images = {str(img.id): img for img in result.scalars().all()}

    # 벡터 검색 순서 유지하면서 응답 생성
    results = []
    for vr in vector_results:
        img = images.get(vr["image_id"])
        if not img:
            continue
        results.append(_image_to_response(img))

    total = len(vector_results) + offset  # 근사치
    return SearchResponse(results=results, total=total, has_more=len(results) == limit)


def _image_to_response(img: Image) -> ImageResponse:
    creator = None
    if img.creator:
        creator = CreatorResponse(
            id=img.creator.id,
            display_name=img.creator.display_name,
            twitter_handle=img.creator.twitter_handle,
            is_verified=img.creator.is_verified,
        )
    return ImageResponse(
        id=img.id,
        thumbnail_url=get_thumbnail_url(img.thumbnail_key) or img.image_url,
        source_url=img.source_url,
        source=img.source,
        tags=img.tags,
        caption=img.caption,
        like_count=img.like_count,
        view_count=img.view_count,
        creator=creator,
    )
