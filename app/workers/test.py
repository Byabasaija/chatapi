# app/workers/test.py
"""
Test tasks for Celery background processing.
Used for testing Celery worker functionality and async operations.
"""
import asyncio

from app.core.celery_app import celery_app


@celery_app.task(acks_late=True, name="app.workers.test.test_celery")
async def test_celery(word: str) -> str:
    """
    Test task for verifying Celery worker functionality.

    Args:
        word: Test string to include in response

    Returns:
        Test response string
    """
    await asyncio.sleep(5)
    return f"test task return {word}"
