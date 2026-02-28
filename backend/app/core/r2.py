import boto3
from app.config import settings


def get_r2_client():
    """Cloudflare R2 클라이언트 (S3 호환)"""
    if not settings.r2_endpoint_url:
        return None
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_key,
    )


def get_thumbnail_url(thumbnail_key: str | None) -> str | None:
    if not thumbnail_key:
        return None
    return f"{settings.r2_public_url}/{thumbnail_key}"
