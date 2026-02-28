from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.image import Image
from app.schemas.image import FeedItem, FeedResponse, ImageResponse
from app.core.r2 import get_thumbnail_url

router = APIRouter()


@router.get("/feed/trending", response_model=FeedResponse)
async def trending_feed(
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """인기 트렌딩 피드 (비개인화, like_count 기반)"""
    stmt = (
        select(Image)
        .where(Image.is_nsfw == False)
        .order_by(Image.like_count.desc(), Image.created_at.desc())
        .limit(limit)
    )

    if cursor:
        # cursor = offset (간단한 구현)
        stmt = stmt.offset(int(cursor))

    result = await db.execute(stmt)
    images = result.scalars().all()

    items = []
    for img in images:
        items.append(FeedItem(
            type="image",
            data=ImageResponse(
                id=img.id,
                thumbnail_url=get_thumbnail_url(img.thumbnail_key) or img.image_url,
                source_url=img.source_url,
                source=img.source,
                tags=img.tags,
                caption=img.caption,
                like_count=img.like_count,
                view_count=img.view_count,
            ),
        ))

    next_cursor = None
    if len(images) == limit:
        current_offset = int(cursor) if cursor else 0
        next_cursor = str(current_offset + limit)

    return FeedResponse(items=items, next_cursor=next_cursor)
