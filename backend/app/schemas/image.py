from uuid import UUID

from pydantic import BaseModel


class CreatorResponse(BaseModel):
    id: UUID
    display_name: str | None = None
    twitter_handle: str | None = None
    is_verified: bool = False

    model_config = {"from_attributes": True}


class ImageResponse(BaseModel):
    id: UUID
    thumbnail_url: str | None = None
    source_url: str
    source: str
    tags: list[str] | None = None
    caption: str | None = None
    like_count: int = 0
    view_count: int = 0
    creator: CreatorResponse | None = None

    model_config = {"from_attributes": True}


class ImageDetailResponse(ImageResponse):
    similar_images: list["ImageResponse"] = []


class SearchResponse(BaseModel):
    results: list[ImageResponse]
    total: int
    has_more: bool


class FeedItem(BaseModel):
    type: str = "image"  # image or ad
    data: ImageResponse


class FeedResponse(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None = None
