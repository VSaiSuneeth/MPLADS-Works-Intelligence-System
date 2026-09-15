import os
import sys
import redis
from rq import Worker, Queue, Connection

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

listen = ["memories", "default"]

if __name__ == "__main__":
    redis_url = settings.REDIS_URL
    print(f"Connecting to Redis at {redis_url}...")
    conn = redis.from_url(redis_url)
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        print("RQ Worker started. Listening for memory processing jobs...")
        worker.work()
