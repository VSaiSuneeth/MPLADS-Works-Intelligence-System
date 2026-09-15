import re
import logging
import numpy as np
from typing import List, Tuple, Dict
from app.services.embedder import get_clip_model, generate_text_embedding, normalize_vector

logger = logging.getLogger(__name__)

# Predefined zero-shot candidate tags
CANDIDATE_TAGS = [
    "Beach & Ocean",
    "Sunset & Sunrise",
    "Mountains & Hiking",
    "Travel & Vacation",
    "City & Architecture",
    "Food & Dining",
    "Coffee & Cafe",
    "Friends & Social",
    "Family",
    "Pets & Animals",
    "Nature & Forest",
    "Party & Nightlife",
    "Documents & Receipts",
    "Music & Concert",
    "Workout & Fitness",
    "Work & Coding",
    "Monsoon & Rain",
    "Historical & Culture",
    "Road Trip",
    "Celebration & Birthday"
]

# Common places dictionary for fast entity detection
KNOWN_PLACES = [
    "Goa", "Mumbai", "Delhi", "Bangalore", "Bengaluru", "Lonavala", "Manali", 
    "Shimla", "Rishikesh", "Jaipur", "Udaipur", "Kerala", "Pondicherry", 
    "Paris", "London", "Tokyo", "New York", "San Francisco", "Dubai", "Singapore",
    "Grand Canyon", "Taj Mahal", "Baga Beach", "Anjuna", "Calangute", "Marine Drive"
]

_candidate_tag_embeddings = None

def get_candidate_tag_embeddings() -> Dict[str, np.ndarray]:
    global _candidate_tag_embeddings
    if _candidate_tag_embeddings is None:
        _candidate_tag_embeddings = {}
        for tag in CANDIDATE_TAGS:
            emb = generate_text_embedding(f"a photo of {tag.lower()}")
            _candidate_tag_embeddings[tag] = np.array(emb, dtype=np.float32)
    return _candidate_tag_embeddings

def auto_tag_from_embedding(embedding: List[float], top_k: int = 3, min_score: float = 0.20) -> List[str]:
    """Auto-tag using cosine similarity between memory embedding and tag embeddings."""
    tag_embs = get_candidate_tag_embeddings()
    emb_arr = np.array(embedding, dtype=np.float32)
    
    scores = []
    for tag, tag_emb in tag_embs.items():
        sim = float(np.dot(emb_arr, tag_emb))
        if sim >= min_score:
            scores.append((tag, sim))
            
    scores.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in scores[:top_k]]

def extract_entities_from_text(text: str) -> List[Dict[str, str]]:
    """Extract location and topic entities from text."""
    if not text:
        return []
    
    entities = []
    # 1. Place matching
    for place in KNOWN_PLACES:
        pattern = rf"\b{re.escape(place)}\b"
        if re.search(pattern, text, re.IGNORECASE):
            entities.append({"name": place, "type": "place", "confidence": 0.95})
            
    # 2. Extract capitalized noun phrases / keywords
    words = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
    for word in set(words):
        if word not in [e["name"] for e in entities] and word not in ["The", "This", "That", "There", "When", "With"]:
            entities.append({"name": word, "type": "topic", "confidence": 0.70})

    return entities[:5]

def reverse_geocode_coords(lat: float, lon: float) -> str:
    """Provide a friendly name for known coordinates."""
    # Well known travel hubs for demo accuracy
    if 14.8 <= lat <= 15.9 and 73.6 <= lon <= 74.4:
        return "Goa, India"
    elif 18.8 <= lat <= 19.3 and 72.7 <= lon <= 73.0:
        return "Mumbai, India"
    elif 18.7 <= lat <= 18.8 and 73.3 <= lon <= 73.5:
        return "Lonavala, India"
    elif 28.4 <= lat <= 28.8 and 77.0 <= lon <= 77.4:
        return "New Delhi, India"
    elif 12.8 <= lat <= 13.1 and 77.4 <= lon <= 77.8:
        return "Bangalore, India"
    elif 48.8 <= lat <= 48.9 and 2.2 <= lon <= 2.5:
        return "Paris, France"
    return f"{lat:.2f}°, {lon:.2f}°"
