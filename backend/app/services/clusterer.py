import math
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np

from app.models.memory import Memory
from app.models.event import Event, EventMemory
from app.models.embedding import Embedding
from app.core.config import settings

logger = logging.getLogger(__name__)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in kilometers."""
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def generate_event_title(memories: List[Memory]) -> str:
    """Generate an intuitive title for an auto-clustered event."""
    # 1. Check for prominent location
    locations = [m.location_name for m in memories if m.location_name]
    location = max(set(locations), key=locations.count) if locations else None

    # 2. Check for prominent place entities
    if not location:
        place_entities = []
        for m in memories:
            for e in m.entities:
                if e.entity and e.entity.type == "place":
                    place_entities.append(e.entity.name)
        if place_entities:
            location = max(set(place_entities), key=place_entities.count)

    # 3. Check for prominent tags
    tags = []
    for m in memories:
        for t in m.tags:
            if t.tag:
                tags.append(t.tag.name.split("&")[0].strip())
    top_tag = max(set(tags), key=tags.count) if tags else "Life Story"

    # 4. Dates
    dates = [m.captured_at or m.created_at for m in memories]
    min_date = min(dates)
    year = min_date.year
    month_name = min_date.strftime("%b")

    if location:
        if "Trip" in location or "Vacation" in location:
            return f"{location} ({year})"
        return f"{location} Trip ({month_name} {year})"
    elif top_tag:
        return f"{top_tag} Moments ({month_name} {year})"
    else:
        return f"Memories ({month_name} {year})"

def auto_cluster_events(db: Session) -> List[Event]:
    """
    Cluster all memories into spatio-temporal events and persist to DB.
    """
    # Fetch all memories ordered by captured_at
    memories = db.query(Memory).order_by(Memory.captured_at.asc()).all()
    if len(memories) < 2:
        return []

    clusters: List[List[Memory]] = []
    current_cluster: List[Memory] = [memories[0]]

    for next_mem in memories[1:]:
        last_mem = current_cluster[-1]
        
        # 1. Temporal closeness (within CLUSTER_TIME_WINDOW_DAYS)
        last_time = last_mem.captured_at or last_mem.created_at
        next_time = next_mem.captured_at or next_mem.created_at
        time_diff_days = abs((next_time - last_time).total_seconds()) / (24 * 3600)

        # 2. Spatial closeness
        is_spatially_close = True
        if (last_mem.latitude is not None and last_mem.longitude is not None and
            next_mem.latitude is not None and next_mem.longitude is not None):
            dist_km = haversine_distance_km(
                last_mem.latitude, last_mem.longitude,
                next_mem.latitude, next_mem.longitude
            )
            is_spatially_close = (dist_km <= settings.CLUSTER_GEO_DISTANCE_KM)

        # Decision: add to current cluster if time difference <= window and spatially close
        if time_diff_days <= settings.CLUSTER_TIME_WINDOW_DAYS and is_spatially_close:
            current_cluster.append(next_mem)
        else:
            if len(current_cluster) >= 2:
                clusters.append(current_cluster)
            current_cluster = [next_mem]

    if len(current_cluster) >= 2:
        clusters.append(current_cluster)

    created_events = []
    for cluster_mems in clusters:
        # Check if an auto-generated event already contains these memories
        first_id = cluster_mems[0].id
        existing_event_mem = db.query(EventMemory).filter(EventMemory.memory_id == first_id).first()
        if existing_event_mem and existing_event_mem.event:
            continue

        dates = [m.captured_at or m.created_at for m in cluster_mems]
        start_date = min(dates)
        end_date = max(dates)
        title = generate_event_title(cluster_mems)
        
        # Find cover photo (preferred photo, otherwise first item)
        photos = [m for m in cluster_mems if m.type == "photo"]
        cover_id = photos[0].id if photos else cluster_mems[0].id

        # Determine location
        locs = [m.location_name for m in cluster_mems if m.location_name]
        location_name = max(set(locs), key=locs.count) if locs else None

        event = Event(
            title=title,
            description=f"Auto-generated cluster containing {len(cluster_mems)} memories.",
            start_date=start_date,
            end_date=end_date,
            location_name=location_name,
            cover_memory_id=cover_id,
            is_auto_generated=True
        )
        db.add(event)
        db.flush()

        for idx, m in enumerate(cluster_mems):
            db.add(EventMemory(
                event_id=event.id,
                memory_id=m.id,
                order_index=idx
            ))

        created_events.append(event)

    db.commit()
    return created_events

def merge_events(db: Session, event_ids: List[str], new_title: Optional[str] = None) -> Optional[Event]:
    """Merge multiple events into a single consolidated event."""
    events = db.query(Event).filter(Event.id.in_(event_ids)).all()
    if not events or len(events) < 2:
        return None

    # Primary event to keep
    primary = events[0]
    all_memories = []
    for ev in events:
        for em in ev.event_memories:
            if em.memory and em.memory not in all_memories:
                all_memories.append(em.memory)

    # Sort memories chronologically
    all_memories.sort(key=lambda m: m.captured_at or m.created_at)

    primary.title = new_title or primary.title
    primary.start_date = min(m.captured_at or m.created_at for m in all_memories)
    primary.end_date = max(m.captured_at or m.created_at for m in all_memories)
    primary.is_auto_generated = False

    # Clear old event memberships and rebuild
    db.query(EventMemory).filter(EventMemory.event_id.in_(event_ids)).delete(synchronize_session=False)
    for idx, m in enumerate(all_memories):
        db.add(EventMemory(event_id=primary.id, memory_id=m.id, order_index=idx))

    # Delete non-primary merged events
    for other in events[1:]:
        db.delete(other)

    db.commit()
    db.refresh(primary)
    return primary
