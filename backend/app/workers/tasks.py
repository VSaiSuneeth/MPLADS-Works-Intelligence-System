import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.storage import storage_backend
from app.models.memory import Memory
from app.models.embedding import Embedding
from app.models.tag import Tag, MemoryTag
from app.models.entity import Entity, MemoryEntity
from app.services.exif_extractor import extract_exif_metadata
from app.services.transcriber import transcribe_audio
from app.services.embedder import generate_image_embedding, generate_text_embedding
from app.services.tagger import auto_tag_from_embedding, extract_entities_from_text, reverse_geocode_coords
from app.services.duplicate_detector import compute_image_phash, find_duplicates_for_memory
from app.services.clusterer import auto_cluster_events

logger = logging.getLogger(__name__)

def process_uploaded_memory(memory_id: str):
    """
    Idempotent background pipeline for processing an uploaded or created memory:
    1. Extracts EXIF metadata & GPS (Photos)
    2. Performs audio transcription (Voice memos)
    3. Computes multi-modal CLIP embeddings (512-dim)
    4. Performs auto-tagging & entity extraction
    5. Calculates perceptual hash & runs duplicate detection
    6. Triggers event clustering update
    """
    db: Session = SessionLocal()
    try:
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            logger.error(f"Memory {memory_id} not found for background processing.")
            return

        logger.info(f"Starting background processing for memory {memory_id} (type: {memory.type}).")

        # 1. Processing by memory type
        vector_512 = None

        if memory.type == "photo" and memory.file_path:
            full_path = storage_backend.get_full_path(memory.file_path)
            
            # Extract EXIF metadata
            exif_res = extract_exif_metadata(full_path)
            if exif_res.get("captured_at"):
                memory.captured_at = exif_res["captured_at"]
                memory.is_captured_at_estimated = False
            else:
                # If no EXIF capture date, keep created_at as captured_at and mark as estimated
                memory.is_captured_at_estimated = True

            if exif_res.get("latitude") and exif_res.get("longitude"):
                memory.latitude = exif_res["latitude"]
                memory.longitude = exif_res["longitude"]
                memory.location_name = reverse_geocode_coords(memory.latitude, memory.longitude)

            # Compute perceptual hash
            phash_str = compute_image_phash(full_path)
            if phash_str:
                memory.phash = phash_str

            # Generate multi-modal image embedding (512-dim)
            vector_512 = generate_image_embedding(full_path)

        elif memory.type == "voice" and memory.file_path:
            full_path = storage_backend.get_full_path(memory.file_path)
            
            # Transcribe audio with Whisper
            transcript, duration = transcribe_audio(full_path)
            memory.transcript = transcript
            if duration:
                memory.duration_seconds = duration

            # Generate multi-modal text embedding on transcript
            text_for_embedding = f"{memory.title or ''}. {transcript}"
            vector_512 = generate_text_embedding(text_for_embedding)

            # Extract entities from transcript
            entities_data = extract_entities_from_text(transcript)
            for ent in entities_data:
                _add_entity_to_memory(db, memory.id, ent["name"], ent["type"], ent["confidence"])

        elif memory.type == "note":
            # Generate multi-modal text embedding on note text
            text_for_embedding = f"{memory.title or ''}. {memory.raw_text or ''}"
            vector_512 = generate_text_embedding(text_for_embedding)

            # Extract entities from note
            entities_data = extract_entities_from_text(memory.raw_text or "")
            for ent in entities_data:
                _add_entity_to_memory(db, memory.id, ent["name"], ent["type"], ent["confidence"])

        # 2. Persist 512-dim Embedding
        if vector_512:
            # Clear old embedding if any
            db.query(Embedding).filter(Embedding.memory_id == memory.id).delete()
            embedding_obj = Embedding(
                memory_id=memory.id,
                vector=vector_512,
                model_name="clip-ViT-B-32"
            )
            db.add(embedding_obj)

            # 3. Auto-tagging using embedding cosine similarity
            tags = auto_tag_from_embedding(vector_512, top_k=3)
            for tag_name in tags:
                _add_tag_to_memory(db, memory.id, tag_name)

        db.commit()
        db.refresh(memory)

        # 4. Duplicate Detection
        find_duplicates_for_memory(memory.id, db)

        # 5. Cluster memories into events
        auto_cluster_events(db)

        logger.info(f"Finished background processing successfully for memory {memory.id}.")

    except Exception as e:
        logger.error(f"Error processing memory {memory_id}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def _add_tag_to_memory(db: Session, memory_id: str, tag_name: str):
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush()
    
    existing = db.query(MemoryTag).filter(MemoryTag.memory_id == memory_id, MemoryTag.tag_id == tag.id).first()
    if not existing:
        db.add(MemoryTag(memory_id=memory_id, tag_id=tag.id, is_user_edited=False))

def _add_entity_to_memory(db: Session, memory_id: str, name: str, ent_type: str, confidence: float):
    entity = db.query(Entity).filter(Entity.name == name, Entity.type == ent_type).first()
    if not entity:
        entity = Entity(name=name, type=ent_type)
        db.add(entity)
        db.flush()

    existing = db.query(MemoryEntity).filter(MemoryEntity.memory_id == memory_id, MemoryEntity.entity_id == entity.id).first()
    if not existing:
        db.add(MemoryEntity(memory_id=memory_id, entity_id=entity.id, confidence=confidence))
