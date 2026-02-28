from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://memetracker:memetracker_dev@localhost:5432/memetracker"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Cloudflare R2
    r2_endpoint_url: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "memetracker"
    r2_public_url: str = "https://r2.memetracker.app"

    # JWT
    jwt_secret: str = "change-me-in-production"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Optional
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
