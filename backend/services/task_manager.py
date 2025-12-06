"""
Task Manager - Track and Cancel AI Generation Tasks
Provides cancellation support for long-running AI operations
"""

import logging
import threading
import time
from typing import Dict, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Task:
    """Represents a single AI generation task"""

    def __init__(self, task_id: str, task_type: str, metadata: Optional[Dict] = None):
        self.task_id = task_id
        self.task_type = task_type  # 'description', 'email', 'bulk_description', 'bulk_email'
        self.status = TaskStatus.PENDING
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result = None
        self.error = None
        self.cancel_flag = threading.Event()  # Thread-safe cancellation flag

    def start(self):
        """Mark task as running"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result=None):
        """Mark task as completed"""
        if not self.is_cancelled():
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now()
            self.result = result

    def fail(self, error: str):
        """Mark task as failed"""
        if not self.is_cancelled():
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.now()
            self.error = error

    def cancel(self):
        """Request cancellation of this task"""
        logger.info(f"Cancellation requested for task {self.task_id}")
        self.cancel_flag.set()
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    def is_cancelled(self) -> bool:
        """Check if task has been cancelled"""
        return self.cancel_flag.is_set()

    def to_dict(self) -> Dict:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class TaskManager:
    """
    Global task manager for tracking and cancelling AI generation tasks
    Thread-safe singleton implementation
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.tasks: Dict[str, Task] = {}
        self.tasks_lock = threading.Lock()
        self._initialized = True
        logger.info("TaskManager initialized")

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_tasks, daemon=True)
        self.cleanup_thread.start()

    def create_task(self, task_id: str, task_type: str, metadata: Optional[Dict] = None) -> Task:
        """Create and register a new task"""
        with self.tasks_lock:
            task = Task(task_id, task_type, metadata)
            self.tasks[task_id] = task
            logger.info(f"Created task {task_id} (type: {task_type})")
            return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self.tasks_lock:
            return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task by ID"""
        task = self.get_task(task_id)
        if task:
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.cancel()
                logger.info(f"Task {task_id} cancelled successfully")
                return True
            else:
                logger.warning(f"Cannot cancel task {task_id} - status: {task.status}")
                return False
        else:
            logger.warning(f"Task {task_id} not found")
            return False

    def remove_task(self, task_id: str):
        """Remove task from registry"""
        with self.tasks_lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.info(f"Removed task {task_id}")

    def get_tasks_by_type(self, task_type: str) -> list[Task]:
        """Get all tasks of a specific type"""
        with self.tasks_lock:
            return [task for task in self.tasks.values() if task.task_type == task_type]

    def get_running_tasks(self) -> list[Task]:
        """Get all currently running tasks"""
        with self.tasks_lock:
            return [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]

    def _cleanup_old_tasks(self):
        """Background thread to clean up old completed/cancelled tasks"""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes

                with self.tasks_lock:
                    now = datetime.now()
                    tasks_to_remove = []

                    for task_id, task in self.tasks.items():
                        # Remove tasks older than 1 hour that are completed/cancelled/failed
                        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]:
                            if task.completed_at:
                                age = (now - task.completed_at).total_seconds()
                                if age > 3600:  # 1 hour
                                    tasks_to_remove.append(task_id)

                    for task_id in tasks_to_remove:
                        del self.tasks[task_id]

                    if tasks_to_remove:
                        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")


# Global task manager instance
task_manager = TaskManager()


def check_cancellation(task_id: str) -> bool:
    """
    Helper function to check if a task has been cancelled
    Returns True if cancelled, False otherwise
    """
    task = task_manager.get_task(task_id)
    if task and task.is_cancelled():
        logger.info(f"Task {task_id} cancellation detected")
        return True
    return False
