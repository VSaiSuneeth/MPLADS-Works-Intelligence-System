import os
import hashlib
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, extract
from pydantic import BaseModel

from app.core.database import get_db
from app.core.storage import storage_backend
from app.models.memory import Memory
from app.models.tag import Tag, MemoryTag
from app.workers.queue import enqueue_job
from app.workers.tasks import process_uploaded_memory

router = APIRouter()

class NoteCreate(BaseModel):
    title: Optional[str] = None
    raw_text: str
    captured_at: Optional[str] = None
    location_name: Optional[str] = None

class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    raw_text: Optional[str] = None
    transcript: Optional[str] = None
    captured_at: Optional[str] = None
    location_name: Optional[str] = None
    is_important: Optional[bool] = None
    tags: Optional[List[str]] = None

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_memory(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    captured_at: Optional[str] = Form(None),
    location_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingest a photo or voice recording file.
    Saves file to storage volume and dispatches background processing job.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Calculate SHA-256 hash
    file_hash = hashlib.sha256(content).hexdigest()

    # Determine type and subfolder from MIME or extension
    content_type = file.content_type or ""
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()

    if content_type.startswith("image/") or ext in [".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif"]:
        mem_type = "photo"
        subfolder = "photos"
    elif content_type.startswith("audio/") or ext in [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".aac"]:
        mem_type = "voice"
        subfolder = "voice"
    elif content_type.startswith("text/") or ext in [".txt", ".md"]:
        mem_type = "note"
        subfolder = "notes"
    else:
        # Default fallback to photo or note
        mem_type = "photo"
        subfolder = "photos"

    # Save to storage
    import io
    file_io = io.BytesIO(content)
    rel_path = storage_backend.save_file(file_io, filename, subfolder=subfolder)

    # Parse provided captured_at or fallback to now
    parsed_captured_at = datetime.utcnow()
    is_estimated = True
    if captured_at:
        try:
            parsed_captured_at = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            is_estimated = False
        except Exception:
            pass

    # Create Memory record
    memory = Memory(
        type=mem_type,
        title=title or filename,
        file_path=rel_path,
        file_hash=file_hash,
        file_size=len(content),
        mime_type=content_type or "application/octet-stream",
        created_at=datetime.utcnow(),
        captured_at=parsed_captured_at,
        is_captured_at_estimated=is_estimated,
        location_name=location_name,
        raw_text=content.decode("utf-8", errors="ignore") if mem_type == "note" else None
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    # Enqueue background job (never blocks upload)
    enqueue_job(process_uploaded_memory, memory.id)

    return memory.to_dict()

@router.post("/note", status_code=status.HTTP_201_CREATED)
def create_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db)
):
    """Directly create a text or markdown note memory."""
    parsed_captured_at = datetime.utcnow()
    is_estimated = True
    if note_in.captured_at:
        try:
            parsed_captured_at = datetime.fromisoformat(note_in.captured_at.replace("Z", "+00:00"))
            is_estimated = False
        except Exception:
            pass

    file_hash = hashlib.sha256(note_in.raw_text.encode("utf-8")).hexdigest()

    memory = Memory(
        type="note",
        title=note_in.title or (note_in.raw_text[:40] + "..." if len(note_in.raw_text) > 40 else "Note"),
        raw_text=note_in.raw_text,
        file_hash=file_hash,
        created_at=datetime.utcnow(),
        captured_at=parsed_captured_at,
        is_captured_at_estimated=is_estimated,
        location_name=note_in.location_name
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    # Enqueue background embedding & tagging
    enqueue_job(process_uploaded_memory, memory.id)

    return memory.to_dict()

@router.get("/timeline")
def get_timeline(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    type_filter: Optional[str] = Query(None),
    important_only: bool = Query(False),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Fetch paginated memories grouped by Year -> Month in chronological order.
    """
    query = db.query(Memory)

    if type_filter and type_filter != "all":
        query = query.filter(Memory.type == type_filter)
    if important_only:
        query = query.filter(Memory.is_important == True)
    if year:
        query = query.filter(extract('year', Memory.captured_at) == year)
    if month:
        query = query.filter(extract('month', Memory.captured_at) == month)

    total = query.count()
    memories = query.order_by(desc(Memory.captured_at)).offset(offset).limit(limit).all()

    # Group into Year -> Month tree
    timeline_tree = {}
    for m in memories:
        dt = m.captured_at or m.created_at
        y = str(dt.year)
        m_name = dt.strftime("%B")
        
        if y not in timeline_tree:
            timeline_tree[y] = {}
        if m_name not in timeline_tree[y]:
            timeline_tree[y][m_name] = []
            
        timeline_tree[y][m_name].append(m.to_dict())

    # Format into list for frontend consumption
    formatted_timeline = []
    for y_key in sorted(timeline_tree.keys(), reverse=True):
        months_list = []
        for m_key, items in timeline_tree[y_key].items():
            months_list.append({
                "month": m_key,
                "count": len(items),
                "items": items
            })
        formatted_timeline.append({
            "year": y_key,
            "months": months_list
        })

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
        "timeline": formatted_timeline,
        "items": [m.to_dict() for m in memories]
    }

@router.get("/file/{file_path:path}")
def get_media_file(file_path: str):
    """Serve media files directly from local storage backend."""
    full_path = storage_backend.get_full_path(file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found on storage disk.")
    return FileResponse(full_path)

@router.get("/{memory_id}")
def get_memory(memory_id: str, db: Session = Depends(get_db)):
    """Fetch single memory by ID with full relations."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return memory.to_dict()

@router.put("/{memory_id}")
def update_memory(
    memory_id: str,
    update_in: MemoryUpdate,
    db: Session = Depends(get_db)
):
    """Update memory metadata, title, tags, or importance."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")

    if update_in.title is not None:
        memory.title = update_in.title
    if update_in.raw_text is not None:
        memory.raw_text = update_in.raw_text
    if update_in.transcript is not None:
        memory.transcript = update_in.transcript
    if update_in.location_name is not None:
        memory.location_name = update_in.location_name
    if update_in.is_important is not None:
        memory.is_important = update_in.is_important
    if update_in.captured_at is not None:
        try:
            memory.captured_at = datetime.fromisoformat(update_in.captured_at.replace("Z", "+00:00"))
            memory.is_captured_at_estimated = False
        except Exception:
            pass

    if update_in.tags is not None:
        # Replace tags
        db.query(MemoryTag).filter(MemoryTag.memory_id == memory.id).delete()
        for tag_name in update_in.tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            db.add(MemoryTag(memory_id=memory.id, tag_id=tag.id, is_user_edited=True))

    db.commit()
    db.refresh(memory)
    return memory.to_dict()

@router.post("/{memory_id}/toggle-favorite")
def toggle_favorite(memory_id: str, db: Session = Depends(get_db)):
    """Toggle is_important status on memory."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")
    memory.is_important = not memory.is_important
    db.commit()
    return {"id": memory.id, "is_important": memory.is_important}

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """Delete memory and corresponding file from disk."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")

    if memory.file_path:
        storage_backend.delete_file(memory.file_path)

    db.delete(memory)
    db.commit()
    return None
