import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    auth_provider: Mapped[str | None] = mapped_column(String(20))  # google, twitter
    auth_id: Mapped[str | None] = mapped_column(String(255))
    is_adult_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    image_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("images.id"))
    action: Mapped[str] = mapped_column(String(20))  # view, like, search_click, share
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_interactions_user", "user_id", created_at.desc()),
    )
