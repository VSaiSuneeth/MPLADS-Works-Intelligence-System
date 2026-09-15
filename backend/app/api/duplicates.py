from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.storage import storage_backend
from app.models.duplicate import DuplicateGroup, DuplicateMember
from app.models.memory import Memory
from app.services.duplicate_detector import find_duplicates_for_memory

router = APIRouter()

class ResolveDuplicateRequest(BaseModel):
    action: str # "keep_primary", "keep_both", "dismiss", "delete_duplicate"
    keep_memory_id: Optional[str] = None
    delete_other: bool = False

@router.get("/")
def list_duplicates(
    status: str = "pending",
    db: Session = Depends(get_db)
):
    """List duplicate groups pending review."""
    groups = db.query(DuplicateGroup).filter(DuplicateGroup.status == status).all()
    return [g.to_dict() for g in groups]

@router.post("/{group_id}/resolve")
def resolve_duplicate(
    group_id: str,
    req: ResolveDuplicateRequest,
    db: Session = Depends(get_db)
):
    """
    Resolve a duplicate group.
    Supports user choosing to dismiss, keep both, or explicitly delete confirmed duplicates.
    """
    group = db.query(DuplicateGroup).filter(DuplicateGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Duplicate group not found.")

    if req.action in ["dismiss", "keep_both"]:
        group.status = "dismissed"
    elif req.action == "keep_primary":
        group.status = "resolved"
        if req.delete_other and req.keep_memory_id:
            # Delete non-kept members only if user explicitly checked delete_other
            for member in list(group.members):
                if member.memory_id != req.keep_memory_id and member.memory:
                    mem = member.memory
                    if mem.file_path:
                        storage_backend.delete_file(mem.file_path)
                    db.delete(mem)

    db.commit()
    return {"message": "Duplicate group resolved.", "group_id": group_id, "status": group.status}

@router.post("/scan")
def scan_all_duplicates(db: Session = Depends(get_db)):
    """Run duplicate detector on all existing memories."""
    memories = db.query(Memory).all()
    detected_count = 0
    for m in memories:
        grp = find_duplicates_for_memory(m.id, db)
        if grp:
            detected_count += 1
    return {"message": f"Scan completed. Checked {len(memories)} memories.", "groups_found": detected_count}
