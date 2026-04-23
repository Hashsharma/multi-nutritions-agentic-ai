# utils/db.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from user_services.app.utils.config import settings

from user_services.app.models.base import Base  # shared Base

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(str(DATABASE_URL), echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
