import os
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ExifTags
import piexif

def _convert_to_degrees(value) -> float:
    """Convert GPS coordinates in (degrees, minutes, seconds) tuple/rational to decimal degrees."""
    try:
        # Check if value is tuple of tuples or floats/ints
        if isinstance(value[0], tuple):
            d0, d1 = value[0]
            d = float(d0) / float(d1)
        else:
            d = float(value[0])

        if isinstance(value[1], tuple):
            m0, m1 = value[1]
            m = float(m0) / float(m1)
        else:
            m = float(value[1])

        if isinstance(value[2], tuple):
            s0, s1 = value[2]
            s = float(s0) / float(s1)
        else:
            s = float(value[2])

        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return 0.0

def extract_exif_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extract capture date, GPS coordinates, and camera metadata from image.
    Returns:
        {
            "captured_at": datetime or None,
            "is_estimated": bool,
            "latitude": float or None,
            "longitude": float or None,
            "camera_model": str or None
        }
    """
    result = {
        "captured_at": None,
        "is_estimated": False,
        "latitude": None,
        "longitude": None,
        "camera_model": None
    }

    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                # Try piexif fallback
                try:
                    raw_exif = piexif.load(image_path)
                    exif_data = {}
                    if "0th" in raw_exif:
                        for tag, val in raw_exif["0th"].items():
                            exif_data[tag] = val
                    if "Exif" in raw_exif:
                        for tag, val in raw_exif["Exif"].items():
                            exif_data[tag] = val
                    if "GPS" in raw_exif:
                        exif_data[34853] = raw_exif["GPS"]
                except Exception:
                    pass

            if not exif_data:
                result["is_estimated"] = True
                return result

            # 1. Extract Capture Date
            # Tags: 36867 (DateTimeOriginal), 36868 (DateTimeDigitized), 306 (DateTime)
            date_str = None
            for tag_id in [36867, 36868, 306]:
                if tag_id in exif_data:
                    date_val = exif_data[tag_id]
                    if isinstance(date_val, bytes):
                        date_str = date_val.decode('utf-8', errors='ignore')
                    elif isinstance(date_val, str):
                        date_str = date_val
                    if date_str:
                        break

            if date_str:
                for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y:%m:%d"]:
                    try:
                        result["captured_at"] = datetime.strptime(date_str.strip("\x00 "), fmt)
                        break
                    except ValueError:
                        continue

            # 2. Extract Camera Info
            make = exif_data.get(271) # Make
            model = exif_data.get(272) # Model
            if isinstance(make, bytes):
                make = make.decode('utf-8', errors='ignore')
            if isinstance(model, bytes):
                model = model.decode('utf-8', errors='ignore')
            if model:
                result["camera_model"] = f"{make} {model}".strip() if make and make not in str(model) else str(model)

            # 3. Extract GPS Coordinates
            # Tag 34853 is GPSInfo
            gps_info = exif_data.get(34853)
            if gps_info:
                # GPSInfo tag keys: 1: LatRef, 2: Lat, 3: LonRef, 4: Lon
                lat_ref = gps_info.get(1) or gps_info.get("GPSLatitudeRef")
                lat_val = gps_info.get(2) or gps_info.get("GPSLatitude")
                lon_ref = gps_info.get(3) or gps_info.get("GPSLongitudeRef")
                lon_val = gps_info.get(4) or gps_info.get("GPSLongitude")

                if lat_val and lon_val:
                    if isinstance(lat_ref, bytes):
                        lat_ref = lat_ref.decode('utf-8', errors='ignore')
                    if isinstance(lon_ref, bytes):
                        lon_ref = lon_ref.decode('utf-8', errors='ignore')

                    lat = _convert_to_degrees(lat_val)
                    lon = _convert_to_degrees(lon_val)

                    if lat_ref and str(lat_ref).upper().startswith("S"):
                        lat = -lat
                    if lon_ref and str(lon_ref).upper().startswith("W"):
                        lon = -lon

                    if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0 and (lat != 0.0 or lon != 0.0):
                        result["latitude"] = round(lat, 6)
                        result["longitude"] = round(lon, 6)

    except Exception:
        pass

    if result["captured_at"] is None:
        result["is_estimated"] = True

    return result
