from __future__ import annotations

import uuid
from pathlib import Path
import re

from backend.core.config import UPLOADS_PATH


def ensure_storage_dirs() -> None:
    Path(UPLOADS_PATH).mkdir(parents=True, exist_ok=True)


def save_uploaded_image(file_bytes: bytes, original_name: str, patient_name: str) -> str:
    ensure_storage_dirs()
    extension = Path(original_name).suffix.lower() or ".png"
    safe_patient_name = re.sub(r"[^A-Za-z0-9]+", "_", patient_name).strip("_") or "patient"
    target_path = Path(UPLOADS_PATH) / f"{safe_patient_name}_{uuid.uuid4().hex[:8]}{extension}"
    with open(target_path, "wb") as f:
        f.write(file_bytes)
    return str(target_path)
