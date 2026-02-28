import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str | None] = mapped_column(String(255))
    twitter_handle: Mapped[str | None] = mapped_column(String(50))
    pixiv_id: Mapped[str | None] = mapped_column(String(50))
    bio: Mapped[str | None] = mapped_column(Text)
    profile_image: Mapped[str | None] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    images: Mapped[list["Image"]] = relationship(back_populates="creator")


class Image(Base):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(20))  # twitter, safebooru, danbooru, manual, upload
    source_id: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    thumbnail_key: Mapped[str | None] = mapped_column(String(255))

    # 메타데이터
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    caption: Mapped[str | None] = mapped_column(Text)
    source_text: Mapped[str | None] = mapped_column(Text)

    # 작가
    creator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("creators.id"))
    creator: Mapped[Creator | None] = relationship(back_populates="images")

    # 분류
    is_nsfw: Mapped[bool] = mapped_column(Boolean, default=False)
    content_type: Mapped[str | None] = mapped_column(String(20))  # meme, illustration, photo

    # 벡터 상태
    clip_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    text_indexed: Mapped[bool] = mapped_column(Boolean, default=False)

    # 통계
    like_count: Mapped[int] = mapped_column(default=0)
    view_count: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
