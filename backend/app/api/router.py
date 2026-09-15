from fastapi import APIRouter
from app.api import memories, search, events, duplicates, reminders

api_router = APIRouter()

api_router.include_router(memories.router, prefix="/memories", tags=["Memories"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(duplicates.router, prefix="/duplicates", tags=["Duplicates"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
