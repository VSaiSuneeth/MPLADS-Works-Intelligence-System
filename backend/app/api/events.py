from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.event import Event, EventMemory
from app.models.memory import Memory
from app.services.clusterer import auto_cluster_events, merge_events

router = APIRouter()

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_name: Optional[str] = None
    cover_memory_id: Optional[str] = None

class EventMergeRequest(BaseModel):
    event_ids: List[str]
    title: Optional[str] = None

class EventSplitRequest(BaseModel):
    split_at_memory_id: str
    new_event_title: Optional[str] = None

@router.get("/")
def list_events(db: Session = Depends(get_db)):
    """List all clustered life events."""
    events = db.query(Event).order_by(Event.start_date.desc()).all()
    
    # Return formatted events with cover thumbnail path
    results = []
    for ev in events:
        d = ev.to_dict(include_memories=False)
        if ev.cover_memory_id:
            cover = db.query(Memory).filter(Memory.id == ev.cover_memory_id).first()
            if cover:
                d["cover_file_path"] = cover.file_path
                d["cover_type"] = cover.type
        results.append(d)
    return results

@router.get("/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Get single event with all child memories."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event.to_dict(include_memories=True)

@router.put("/{event_id}")
def update_event(event_id: str, event_in: EventUpdate, db: Session = Depends(get_db)):
    """Rename or edit description of an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    if event_in.title is not None:
        event.title = event_in.title
        event.is_auto_generated = False
    if event_in.description is not None:
        event.description = event_in.description
    if event_in.location_name is not None:
        event.location_name = event_in.location_name
    if event_in.cover_memory_id is not None:
        event.cover_memory_id = event_in.cover_memory_id

    db.commit()
    db.refresh(event)
    return event.to_dict(include_memories=True)

@router.post("/merge")
def merge_events_endpoint(req: EventMergeRequest, db: Session = Depends(get_db)):
    """Merge multiple events into one."""
    merged = merge_events(db, req.event_ids, req.title)
    if not merged:
        raise HTTPException(status_code=400, detail="Could not merge specified events.")
    return merged.to_dict(include_memories=True)

@router.post("/{event_id}/split")
def split_event(event_id: str, req: EventSplitRequest, db: Session = Depends(get_db)):
    """Split an event at a specified memory ID."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    sorted_mems = sorted(event.event_memories, key=lambda x: x.order_index)
    split_idx = next((i for i, em in enumerate(sorted_mems) if em.memory_id == req.split_at_memory_id), None)

    if split_idx is None or split_idx == 0:
        raise HTTPException(status_code=400, detail="Invalid split position.")

    part1 = sorted_mems[:split_idx]
    part2 = sorted_mems[split_idx:]

    # Create new event for part2
    part2_memories = [em.memory for em in part2 if em.memory]
    new_event = Event(
        title=req.new_event_title or f"{event.title} (Part 2)",
        start_date=min(m.captured_at or m.created_at for m in part2_memories),
        end_date=max(m.captured_at or m.created_at for m in part2_memories),
        location_name=event.location_name,
        cover_memory_id=part2_memories[0].id if part2_memories else None,
        is_auto_generated=False
    )
    db.add(new_event)
    db.flush()

    for idx, em in enumerate(part2):
        em.event_id = new_event.id
        em.order_index = idx

    # Update original event end date
    part1_memories = [em.memory for em in part1 if em.memory]
    event.end_date = max(m.captured_at or m.created_at for m in part1_memories)
    event.is_auto_generated = False

    db.commit()
    return {
        "event_1": event.to_dict(include_memories=True),
        "event_2": new_event.to_dict(include_memories=True)
    }

@router.post("/recluster")
def recluster(db: Session = Depends(get_db)):
    """Trigger spatio-temporal event clustering across all memories."""
    events = auto_cluster_events(db)
    return {"message": f"Clustered memories into {len(events)} new events.", "count": len(events)}

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    """Delete an event without deleting the underlying memories."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    db.delete(event)
    db.commit()
    return None
