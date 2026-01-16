"""Progress tracking manager for upload tasks."""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class UploadProgress:
    """Upload progress state."""
    task_id: str
    file_name: str
    total_pages: int = 0
    current_page: int = 0
    status: str = "pending"  # pending, extracting, processing, complete, error
    message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProgressManager:
    """Manager for tracking upload progress with SSE support."""

    def __init__(self):
        self._tasks: Dict[str, UploadProgress] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    def create_task(self, task_id: str, file_name: str) -> UploadProgress:
        """Create a new progress tracking task."""
        progress = UploadProgress(task_id=task_id, file_name=file_name)
        self._tasks[task_id] = progress
        self._subscribers[task_id] = []
        logger.info(f"Created progress task: {task_id} for {file_name}")
        return progress

    async def update_progress(
        self,
        task_id: str,
        current_page: int = None,
        total_pages: int = None,
        status: str = None,
        message: str = None,
        result: Dict = None,
        error: str = None
    ):
        """Update progress and notify all subscribers."""
        if task_id not in self._tasks:
            logger.warning(f"Task not found: {task_id}")
            return

        progress = self._tasks[task_id]

        if current_page is not None:
            progress.current_page = current_page
        if total_pages is not None:
            progress.total_pages = total_pages
        if status is not None:
            progress.status = status
        if message is not None:
            progress.message = message
        if result is not None:
            progress.result = result
        if error is not None:
            progress.error = error

        # Notify all subscribers
        event = self._format_event(progress)
        for queue in self._subscribers.get(task_id, []):
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Failed to notify subscriber: {e}")

    def _format_event(self, progress: UploadProgress) -> Dict[str, Any]:
        """Format progress as event data."""
        return {
            "task_id": progress.task_id,
            "file_name": progress.file_name,
            "status": progress.status,
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "message": progress.message,
            "result": progress.result,
            "error": progress.error
        }

    def subscribe(self, task_id: str) -> asyncio.Queue:
        """Subscribe to progress updates for a task."""
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        queue = asyncio.Queue()
        self._subscribers[task_id].append(queue)
        logger.debug(f"New subscriber for task: {task_id}")
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        """Unsubscribe from progress updates."""
        if task_id in self._subscribers:
            try:
                self._subscribers[task_id].remove(queue)
                logger.debug(f"Unsubscribed from task: {task_id}")
            except ValueError:
                pass

    def get_progress(self, task_id: str) -> Optional[UploadProgress]:
        """Get current progress for a task."""
        return self._tasks.get(task_id)

    def cleanup_task(self, task_id: str):
        """Remove a completed task from tracking."""
        self._tasks.pop(task_id, None)
        self._subscribers.pop(task_id, None)
        logger.debug(f"Cleaned up task: {task_id}")


# Global singleton instance
progress_manager = ProgressManager()
