import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
import numpy as np

from app.models.memory import Memory
from app.models.embedding import Embedding
from app.models.tag import Tag, MemoryTag
from app.models.entity import Entity, MemoryEntity
from app.services.embedder import generate_text_embedding
from app.core.database import IS_POSTGRES

logger = logging.getLogger(__name__)

def parse_query_metadata_hints(query: str) -> Dict[str, Any]:
    """Extract dates, locations, and type filters from natural language query."""
    hints = {
        "year": None,
        "type": None,
        "locations": []
    }
    
    # 1. Year matching (e.g., 2023, 2024, 2025, 2026)
    year_match = re.search(r'\b(20\d\d)\b', query)
    if year_match:
        hints["year"] = int(year_match.group(1))

    # 2. Type matching
    q_lower = query.lower()
    if any(w in q_lower for w in ["photo", "photos", "picture", "pictures", "image", "images"]):
        hints["type"] = "photo"
    elif any(w in q_lower for w in ["note", "notes", "writing", "journal", "thoughts"]):
        hints["type"] = "note"
    elif any(w in q_lower for w in ["voice", "audio", "recording", "memo", "memos", "podcast"]):
        hints["type"] = "voice"

    # 3. Known locations
    from app.services.tagger import KNOWN_PLACES
    for place in KNOWN_PLACES:
        if re.search(rf"\b{re.escape(place)}\b", query, re.IGNORECASE):
            hints["locations"].append(place)

    return hints

def search_memories(
    query: str,
    db: Session,
    type_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 30
) -> List[Dict[str, Any]]:
    """
    Perform semantic search across all memories (photos, notes, voice memos)
    using unified CLIP multi-modal vector space + temporal/spatial boosting.
    """
    query = query.strip()
    if not query:
        # Return recent memories
        q = db.query(Memory).order_by(Memory.captured_at.desc()).limit(limit)
        return [{"memory": m.to_dict(), "score": 1.0} for m in q.all()]

    hints = parse_query_metadata_hints(query)
    effective_type = type_filter or hints["type"]

    # 1. Generate query embedding (512-dim)
    q_vec = np.array(generate_text_embedding(query), dtype=np.float32)

    # 2. Query candidates from database
    base_query = db.query(Memory)
    
    if effective_type:
        base_query = base_query.filter(Memory.type == effective_type)
    if date_from:
        base_query = base_query.filter(Memory.captured_at >= date_from)
    if date_to:
        base_query = base_query.filter(Memory.captured_at <= date_to)
    if tag_filter:
        base_query = base_query.join(Memory.tags).join(MemoryTag.tag).filter(Tag.name.ilike(f"%{tag_filter}%"))

    memories = base_query.all()
    if not memories:
        return []

    # 3. Calculate semantic cosine similarity scores
    scored_results = []
    
    for mem in memories:
        # Base vector similarity
        sim_score = 0.0
        if mem.embeddings:
            emb = mem.embeddings[0]
            m_vec = np.array(emb.get_vector_list(), dtype=np.float32)
            if len(m_vec) == len(q_vec) and np.linalg.norm(m_vec) > 0:
                sim_score = float(np.dot(q_vec, m_vec))

        # Text keyword match boost (for title, raw_text, transcript)
        text_content = f"{mem.title or ''} {mem.raw_text or ''} {mem.transcript or ''} {mem.location_name or ''}".lower()
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        
        keyword_hits = sum(1 for w in query_words if w in text_content)
        if keyword_hits > 0:
            sim_score += (keyword_hits * 0.08)

        # Year boost if query mentioned year
        if hints["year"] and mem.captured_at and mem.captured_at.year == hints["year"]:
            sim_score += 0.15

        # Location boost if query mentioned location
        if hints["locations"]:
            for loc in hints["locations"]:
                if mem.location_name and loc.lower() in mem.location_name.lower():
                    sim_score += 0.20
                    break
                elif any(e.entity and loc.lower() in e.entity.name.lower() for e in mem.entities):
                    sim_score += 0.20
                    break

        scored_results.append({
            "memory": mem.to_dict(),
            "score": round(float(sim_score), 4)
        })

    # Sort by relevance score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:limit]
