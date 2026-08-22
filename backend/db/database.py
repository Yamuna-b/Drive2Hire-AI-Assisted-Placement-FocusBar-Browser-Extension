from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import DATABASE_URL

Base = declarative_base()
engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)
    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )


async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured — set DATABASE_URL in .env")
    async with AsyncSessionLocal() as session:
        yield session
