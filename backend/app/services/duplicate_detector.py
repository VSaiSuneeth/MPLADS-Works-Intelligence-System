import logging
from typing import List, Optional
import imagehash
from PIL import Image
from sqlalchemy.orm import Session
import numpy as np

from app.models.memory import Memory
from app.models.duplicate import DuplicateGroup, DuplicateMember
from app.models.embedding import Embedding
from app.core.config import settings

logger = logging.getLogger(__name__)

def compute_image_phash(image_path: str) -> Optional[str]:
    """Compute perceptual hash (pHash) for an image."""
    try:
        with Image.open(image_path) as img:
            h = imagehash.phash(img)
            return str(h)
    except Exception as e:
        logger.error(f"Error computing pHash for {image_path}: {e}")
        return None

def compute_phash_distance(hash1_str: str, hash2_str: str) -> int:
    """Compute Hamming distance between two hex pHash strings."""
    try:
        h1 = imagehash.hex_to_hash(hash1_str)
        h2 = imagehash.hex_to_hash(hash2_str)
        return h1 - h2
    except Exception:
        return 999

def find_duplicates_for_memory(memory_id: str, db: Session) -> Optional[DuplicateGroup]:
    """
    Check if the target memory is an exact or near duplicate of any existing memory.
    If matches are found, group them in a DuplicateGroup and return it.
    """
    target = db.query(Memory).filter(Memory.id == memory_id).first()
    if not target:
        return None

    # Check if target is already in an active duplicate group
    existing_member = db.query(DuplicateMember).filter(DuplicateMember.memory_id == memory_id).first()
    if existing_member:
        return existing_member.group

    other_memories = db.query(Memory).filter(Memory.id != memory_id).all()
    matched_members = [] # (other_memory, similarity_score, duplicate_type)

    for other in other_memories:
        # 1. Exact SHA-256 hash match
        if target.file_hash and other.file_hash and target.file_hash == other.file_hash:
            matched_members.append((other, 1.0, "exact_hash"))
            continue

        # 2. Image pHash match
        if target.phash and other.phash:
            dist = compute_phash_distance(target.phash, other.phash)
            if dist <= settings.PHASH_HAMMING_THRESHOLD:
                # Convert distance to similarity score (dist 0 = 1.0, dist 6 = 0.90)
                sim = round(max(0.85, 1.0 - (dist / 64.0)), 3)
                matched_members.append((other, sim, "phash_match"))
                continue

    # 3. If no exact/phash match, check high cosine embedding similarity
    if not matched_members:
        target_emb = db.query(Embedding).filter(Embedding.memory_id == memory_id).first()
        if target_emb:
            t_vec = np.array(target_emb.get_vector_list(), dtype=np.float32)
            for other in other_memories:
                o_emb = db.query(Embedding).filter(Embedding.memory_id == other.id).first()
                if o_emb:
                    o_vec = np.array(o_emb.get_vector_list(), dtype=np.float32)
                    sim = float(np.dot(t_vec, o_vec))
                    if sim >= settings.EMBEDDING_SIMILARITY_THRESHOLD:
                        matched_members.append((other, round(sim, 3), "embedding_similarity"))

    if not matched_members:
        return None

    # Check if any matched memory is already in a duplicate group
    group = None
    for other, _, _ in matched_members:
        other_m = db.query(DuplicateMember).filter(DuplicateMember.memory_id == other.id).first()
        if other_m and other_m.group:
            group = other_m.group
            break

    if not group:
        group = DuplicateGroup(status="pending")
        db.add(group)
        db.flush()

        # Add the first matched member as primary
        first_other, _, _ = matched_members[0]
        db.add(DuplicateMember(
            group_id=group.id,
            memory_id=first_other.id,
            similarity_score=1.0,
            duplicate_type="original",
            is_primary=True
        ))

    # Add target memory to the group
    best_match = max(matched_members, key=lambda x: x[1])
    db.add(DuplicateMember(
        group_id=group.id,
        memory_id=target.id,
        similarity_score=best_match[1],
        duplicate_type=best_match[2],
        is_primary=False
    ))

    db.commit()
    db.refresh(group)
    return group
