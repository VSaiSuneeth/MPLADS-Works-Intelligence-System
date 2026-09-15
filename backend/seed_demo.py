import os
import io
import hashlib
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import piexif

from app.core.database import SessionLocal, init_db
from app.core.storage import storage_backend
from app.models.memory import Memory
from app.workers.tasks import process_uploaded_memory
from app.services.clusterer import auto_cluster_events

def create_color_photo_with_exif(
    text: str,
    bg_color: tuple,
    captured_date_str: str,
    lat: float = 15.4989,
    lon: float = 73.8278,
    camera_model: str = "Sony Alpha 7 IV"
) -> bytes:
    img = Image.new("RGB", (600, 450), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Decorative shapes
    draw.rectangle([20, 20, 580, 430], outline=(255, 255, 255), width=3)
    draw.ellipse([250, 80, 350, 180], fill=(255, 200, 50))
    draw.polygon([(50, 400), (200, 250), (350, 400)], fill=(40, 80, 120))
    draw.polygon([(250, 400), (420, 200), (550, 400)], fill=(30, 60, 100))
    draw.text((40, 380), text, fill=(255, 255, 255))

    def to_deg(val):
        deg = int(abs(val))
        min_f = (abs(val) - deg) * 60
        min_i = int(min_f)
        sec_i = int((min_f - min_i) * 60 * 100)
        return ((deg, 1), (min_i, 1), (sec_i, 100))

    zeroth_ifd = {
        piexif.ImageIFD.Make: b"Sony",
        piexif.ImageIFD.Model: camera_model.encode('utf-8')
    }
    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: captured_date_str.encode('utf-8'),
        piexif.ExifIFD.DateTimeDigitized: captured_date_str.encode('utf-8'),
    }
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude: to_deg(lat),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude: to_deg(lon),
    }

    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd}
    exif_bytes = piexif.dump(exif_dict)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()

def seed_vault():
    print("Initializing database and seeding rich demonstration memories...")
    init_db()
    db = SessionLocal()

    # 1. 2025 Goa Trip - Photo 1 (Anjuna Beach Sunset)
    p1_bytes = create_color_photo_with_exif(
        "Sunset over Anjuna Beach, Goa",
        (230, 100, 60),
        "2025:01:14 18:25:00",
        lat=15.5800,
        lon=73.7400
    )
    p1_hash = hashlib.sha256(p1_bytes).hexdigest()
    p1_path = storage_backend.save_file(io.BytesIO(p1_bytes), "anjuna_sunset.jpg", subfolder="photos")
    m1 = Memory(
        type="photo",
        title="Anjuna Beach Golden Sunset",
        file_path=p1_path,
        file_hash=p1_hash,
        file_size=len(p1_bytes),
        mime_type="image/jpeg",
        captured_at=datetime(2025, 1, 14, 18, 25, 0),
        is_captured_at_estimated=False,
        is_important=True
    )
    db.add(m1)
    db.commit()
    process_uploaded_memory(m1.id)

    # 2. 2025 Goa Trip - Photo 2 (Baga Beach Cafe)
    p2_bytes = create_color_photo_with_exif(
        "Seafood and Coffee at Baga Beach",
        (40, 130, 170),
        "2025:01:15 13:10:00",
        lat=15.5553,
        lon=73.7517
    )
    p2_hash = hashlib.sha256(p2_bytes).hexdigest()
    p2_path = storage_backend.save_file(io.BytesIO(p2_bytes), "baga_cafe.jpg", subfolder="photos")
    m2 = Memory(
        type="photo",
        title="Lunch at Baga Beach Shack",
        file_path=p2_path,
        file_hash=p2_hash,
        file_size=len(p2_bytes),
        mime_type="image/jpeg",
        captured_at=datetime(2025, 1, 15, 13, 10, 0),
        is_captured_at_estimated=False,
        is_important=False
    )
    db.add(m2)
    db.commit()
    process_uploaded_memory(m2.id)

    # 3. 2025 Goa Trip - Note
    m3 = Memory(
        type="note",
        title="Goa Trip Highlights & Reflections",
        raw_text="The sunset at Anjuna yesterday was magical. We rode scooters along the coast from Calangute to Vagator. Trying authentic fish curry with local spices in Goa.",
        file_hash=hashlib.sha256(b"Goa Trip Reflections").hexdigest(),
        captured_at=datetime(2025, 1, 15, 21, 0, 0),
        is_captured_at_estimated=False,
        location_name="Goa, India",
        is_important=True
    )
    db.add(m3)
    db.commit()
    process_uploaded_memory(m3.id)

    # 4. 2025 Goa Trip - Voice Memo
    m4 = Memory(
        type="voice",
        title="Voice Memo: Ocean waves and thoughts on life",
        raw_text="Voice recording transcript: Sitting on the rocks listening to the waves crash in North Goa. Clear breeze, feeling refreshed and inspired for the new year.",
        transcript="Sitting on the rocks listening to the waves crash in North Goa. Clear breeze, feeling refreshed and inspired for the new year.",
        duration_seconds=38.5,
        file_hash=hashlib.sha256(b"Voice Memo Ocean").hexdigest(),
        captured_at=datetime(2025, 1, 16, 8, 30, 0),
        is_captured_at_estimated=False,
        location_name="Goa, India",
        is_important=False
    )
    db.add(m4)
    db.commit()
    process_uploaded_memory(m4.id)

    # 5. Duplicate photo for duplicate detection review
    p5_dup_bytes = create_color_photo_with_exif(
        "Sunset over Anjuna Beach, Goa (Burst Shot)",
        (230, 100, 60), # Exact image layout
        "2025:01:14 18:25:02",
        lat=15.5800,
        lon=73.7400
    )
    p5_hash = hashlib.sha256(p5_dup_bytes).hexdigest()
    p5_path = storage_backend.save_file(io.BytesIO(p5_dup_bytes), "anjuna_sunset_burst.jpg", subfolder="photos")
    m5 = Memory(
        type="photo",
        title="Anjuna Beach Golden Sunset (Burst)",
        file_path=p5_path,
        file_hash=p5_hash,
        file_size=len(p5_dup_bytes),
        mime_type="image/jpeg",
        captured_at=datetime(2025, 1, 14, 18, 25, 2),
        is_captured_at_estimated=False,
        is_important=False
    )
    db.add(m5)
    db.commit()
    process_uploaded_memory(m5.id)

    # 6. Flashback Memory (1 year ago)
    past_date = datetime.now() - timedelta(days=365)
    p6_bytes = create_color_photo_with_exif(
        "Mountain Trek in Lonavala",
        (34, 139, 34),
        past_date.strftime("%Y:%m:%d 11:00:00"),
        lat=18.7500,
        lon=73.4000
    )
    p6_hash = hashlib.sha256(p6_bytes).hexdigest()
    p6_path = storage_backend.save_file(io.BytesIO(p6_bytes), "lonavala_trek.jpg", subfolder="photos")
    m6 = Memory(
        type="photo",
        title="Tiger Point Trek in Lonavala",
        file_path=p6_path,
        file_hash=p6_hash,
        file_size=len(p6_bytes),
        mime_type="image/jpeg",
        captured_at=past_date,
        is_captured_at_estimated=False,
        location_name="Lonavala, India",
        is_important=True
    )
    db.add(m6)
    db.commit()
    process_uploaded_memory(m6.id)

    # Trigger clustering
    auto_cluster_events(db)
    db.close()
    print("Demo seed completed successfully! All memories, embeddings, and clusters are created.")

if __name__ == "__main__":
    seed_vault()
