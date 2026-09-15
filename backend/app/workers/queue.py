import logging
import threading
from typing import Callable, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_conn = None
_task_queue = None

def get_redis_connection():
    global _redis_conn
    if _redis_conn is None:
        try:
            import redis
            _redis_conn = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            _redis_conn.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Redis is unreachable ({e}). Local in-memory background worker will be used.")
            _redis_conn = False
    return _redis_conn

def get_task_queue():
    global _task_queue
    if _task_queue is None:
        conn = get_redis_connection()
        if conn:
            try:
                from rq import Queue
                _task_queue = Queue("memories", connection=conn)
                logger.info("Initialized RQ task queue: memories")
            except Exception as e:
                logger.warning(f"Could not initialize RQ Queue: {e}")
                _task_queue = False
        else:
            _task_queue = False
    return _task_queue

def enqueue_job(func: Callable, *args, **kwargs) -> Any:
    """
    Enqueue a background job via Redis + RQ if available,
    otherwise dispatch in an asynchronous background thread.
    Never blocks the caller.
    """
    queue = get_task_queue()
    if queue:
        try:
            job = queue.enqueue(func, *args, **kwargs)
            logger.info(f"Enqueued job {job.id} to RQ.")
            return job.id
        except Exception as e:
            logger.warning(f"RQ enqueue failed: {e}. Falling back to background thread.")

    # In-memory background thread fallback
    def thread_runner():
        try:
            func(*args, **kwargs)
        except Exception as err:
            logger.error(f"Background thread job failed: {err}", exc_info=True)

    thread = threading.Thread(target=thread_runner, daemon=True)
    thread.start()
    return f"thread-{thread.ident}"
