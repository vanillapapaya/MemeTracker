from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.qdrant import qdrant

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    checks = {"status": "ok"}

    # DB 체크
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        checks["status"] = "degraded"

    # Qdrant 체크
    try:
        qdrant.get_collections()
        checks["qdrant"] = "ok"
    except Exception:
        checks["qdrant"] = "error"
        checks["status"] = "degraded"

    return checks
