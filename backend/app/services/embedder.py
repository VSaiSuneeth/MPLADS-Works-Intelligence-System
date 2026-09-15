import logging
import numpy as np
from PIL import Image
from typing import Union, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_clip_model = None

def get_clip_model():
    global _clip_model
    if _clip_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # clip-ViT-B-32 maps both images and text into the exact same 512-dim vector space
            logger.info(f"Loading multi-modal CLIP model: {settings.CLIP_MODEL_NAME}...")
            _clip_model = SentenceTransformer(settings.CLIP_MODEL_NAME)
            logger.info("CLIP model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer CLIP model: {e}. Using deterministic feature fallback.")
            _clip_model = False
    return _clip_model

def normalize_vector(vec: np.ndarray) -> np.ndarray:
    """Normalize vector to unit length (L2 norm)."""
    norm = np.linalg.norm(vec)
    if norm > 0:
        return vec / norm
    return vec

def generate_image_embedding(image_path_or_pil: Union[str, Image.Image]) -> List[float]:
    """Generate 512-dimensional normalized embedding for an image."""
    model = get_clip_model()
    
    if isinstance(image_path_or_pil, str):
        try:
            image = Image.open(image_path_or_pil).convert("RGB")
        except Exception as e:
            logger.error(f"Error opening image {image_path_or_pil}: {e}")
            return [0.0] * 512
    else:
        image = image_path_or_pil.convert("RGB")

    if model:
        try:
            embedding = model.encode(image)
            norm_emb = normalize_vector(np.array(embedding, dtype=np.float32))
            return norm_emb.tolist()
        except Exception as e:
            logger.error(f"Error generating CLIP image embedding: {e}")

    # Deterministic fallback embedding from color histogram + resized thumbnail
    try:
        thumb = image.resize((16, 16)).convert("L")
        pixels = np.array(thumb, dtype=np.float32).flatten() # 256 dims
        hist = np.array(image.histogram()[:256], dtype=np.float32) # 256 dims
        combined = np.concatenate([pixels, hist]) # 512 dims
        return normalize_vector(combined).tolist()
    except Exception:
        return [0.0] * 512

def generate_text_embedding(text: str) -> List[float]:
    """Generate 512-dimensional normalized embedding for text (note, transcript, or search query)."""
    if not text or not text.strip():
        return [0.0] * 512

    model = get_clip_model()
    if model:
        try:
            embedding = model.encode(text.strip())
            norm_emb = normalize_vector(np.array(embedding, dtype=np.float32))
            return norm_emb.tolist()
        except Exception as e:
            logger.error(f"Error generating CLIP text embedding: {e}")

    # Deterministic fallback text embedding via hashing character n-grams
    import hashlib
    np.random.seed(int(hashlib.md5(text.encode('utf-8')).hexdigest()[:8], 16))
    vec = np.random.randn(512).astype(np.float32)
    return normalize_vector(vec).tolist()
