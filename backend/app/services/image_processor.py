import io
import uuid
from datetime import datetime

import httpx
from PIL import Image as PILImage

from app.core.r2 import get_r2_client
from app.config import settings


async def download_image(url: str) -> bytes:
    """이미지 URL에서 다운로드"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True, timeout=30)
        response.raise_for_status()
        return response.content


def resize_image(image_bytes: bytes, size: tuple[int, int] = (400, 400)) -> bytes:
    """이미지 리사이즈 → WebP"""
    img = PILImage.open(io.BytesIO(image_bytes))
    img.thumbnail(size, PILImage.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=85)
    return buffer.getvalue()


def upload_to_r2(image_bytes: bytes, source: str) -> str | None:
    """R2에 썸네일 업로드, 키 반환"""
    client = get_r2_client()
    if not client:
        return None

    now = datetime.utcnow()
    key = f"thumbnails/{source}/{now:%Y-%m}/{uuid.uuid4()}.webp"
    client.put_object(
        Bucket=settings.r2_bucket,
        Key=key,
        Body=image_bytes,
        ContentType="image/webp",
    )
    return key
