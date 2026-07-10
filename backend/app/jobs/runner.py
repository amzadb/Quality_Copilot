"""Background task runner — FastAPI BackgroundTasks for MVP."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks


class JobRunner:
    """Enqueue work via FastAPI BackgroundTasks.

    Swap for Celery/RQ/Arq when you need retries, concurrency limits, or multi-worker scaling.
    """

    def __init__(self, background_tasks: BackgroundTasks | None = None) -> None:
        self._background_tasks = background_tasks

    def enqueue(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        job_id = str(uuid4())
        if self._background_tasks is not None:
            self._background_tasks.add_task(task, *args, job_id=job_id, **kwargs)
        return job_id

    async def run_inline(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run synchronously when no BackgroundTasks context is available."""
        return await task(*args, **kwargs) if _is_coroutine_function(task) else task(*args, **kwargs)


def _is_coroutine_function(func: Callable[..., Any]) -> bool:
    import asyncio

    return asyncio.iscoroutinefunction(func)


def get_job_runner(background_tasks: BackgroundTasks) -> JobRunner:
    return JobRunner(background_tasks)
