import asyncio

from app.core.celery_app import celery_app


@celery_app.task(acks_late=True)
async def test_celery(word: str) -> str:
    await asyncio.sleep(5)
    return f"test task return {word}"
