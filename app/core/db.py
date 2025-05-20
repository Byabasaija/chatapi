from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI), echo=False, future=True
)


# Create a sessionmaker for async sessions
async_session_maker = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables uncommenting the next lines
    # async with async_engine.begin() as conn:
    #     await conn.run_sync(SQLModel.metadata.create_all)
    pass
