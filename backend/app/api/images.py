from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.image import Image
from app.schemas.image import ImageDetailResponse, ImageResponse, CreatorResponse
from app.services.vector_search import similar_images
from app.core.r2 import get_thumbnail_url

router = APIRouter()


@router.get("/images/{image_id}", response_model=ImageDetailResponse)
async def get_image(image_id: UUID, db: AsyncSession = Depends(get_db)):
    """이미지 상세 정보 + 비슷한 짤"""
    stmt = select(Image).where(Image.id == image_id).options(selectinload(Image.creator))
    result = await db.execute(stmt)
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

    # 비슷한 이미지 검색
    similar = []
    if img.clip_indexed:
        try:
            sim_results = similar_images(str(img.id), limit=8)
            sim_ids = [s["image_id"] for s in sim_results]
            if sim_ids:
                stmt2 = select(Image).where(Image.id.in_(sim_ids))
                result2 = await db.execute(stmt2)
                sim_images = {str(i.id): i for i in result2.scalars().all()}
                similar = [_image_to_response(sim_images[sid]) for sid in sim_ids if sid in sim_images]
        except Exception:
            pass  # 유사 이미지 실패해도 상세 정보는 반환

    creator = None
    if img.creator:
        creator = CreatorResponse(
            id=img.creator.id,
            display_name=img.creator.display_name,
            twitter_handle=img.creator.twitter_handle,
            is_verified=img.creator.is_verified,
        )

    return ImageDetailResponse(
        id=img.id,
        thumbnail_url=get_thumbnail_url(img.thumbnail_key) or img.image_url,
        source_url=img.source_url,
        source=img.source,
        tags=img.tags,
        caption=img.caption,
        like_count=img.like_count,
        view_count=img.view_count,
        creator=creator,
        similar_images=similar,
    )


def _image_to_response(img: Image) -> ImageResponse:
    return ImageResponse(
        id=img.id,
        thumbnail_url=get_thumbnail_url(img.thumbnail_key) or img.image_url,
        source_url=img.source_url,
        source=img.source,
        tags=img.tags,
        caption=img.caption,
        like_count=img.like_count,
        view_count=img.view_count,
    )
