import logging

from sqlalchemy import text

from backend.config import DATABASE_URL
from backend.db.database import Base, engine
import backend.models  # noqa: F401 — register models with Base.metadata

logger = logging.getLogger(__name__)


async def init_db() -> bool:
    """Create all tables if PostgreSQL is reachable. Returns True on success."""
    if not DATABASE_URL or engine is None:
        logger.info("DATABASE_URL not set — running without PostgreSQL (OK for Phase 1/2)")
        return False

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("SELECT 1"))
        logger.info("Database tables ready")
        return True
    except Exception as exc:
        logger.warning("Database not available: %s", exc)
        return False
