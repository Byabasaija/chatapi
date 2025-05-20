import asyncio
import logging

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncEngine
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import async_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def init(db_engine: AsyncEngine) -> None:
    try:
        # Create async session and check if DB is awake
        async with db_engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
    except Exception as e:
        logger.error(e)
        raise e


async def main() -> None:
    logger.info("Initializing service")
    await init(async_engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    asyncio.run(main())
