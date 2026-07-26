from fastapi import APIRouter
from sqlalchemy import text

from app.database import async_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return {"status": "degraded", "db": "unreachable"}
    return {"status": "ok"}
