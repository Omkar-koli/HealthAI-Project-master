from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path
from typing import Optional

from backend.core.config import GCP_PROJECT, GCS_BUCKET, STORAGE_BACKEND, UPLOADS_PATH


class StorageError(RuntimeError):
    """Raised when an upload cannot be stored or read back."""


_bucket = None


def _get_bucket():
    """Lazily create the bucket handle using Application Default Credentials
    (the VM's service account via the metadata server; no key file)."""
    global _bucket
    if _bucket is None:
        from google.cloud import storage

        _bucket = storage.Client(project=GCP_PROJECT or None).bucket(GCS_BUCKET)
    return _bucket


def _new_filename(original_name: str, patient_name: str) -> str:
    extension = Path(original_name).suffix.lower() or ".png"
    safe_patient_name = re.sub(r"[^A-Za-z0-9]+", "_", patient_name).strip("_") or "patient"
    return f"{safe_patient_name}_{uuid.uuid4().hex[:8]}{extension}"


def save_uploaded_image(file_bytes: bytes, original_name: str, patient_name: str) -> str:
    """Store the upload and return the reference saved in studies.image_path.

    gcs   -> object name inside the bucket, e.g. 'uploads/Jane_ab12cd34.png'
    local -> absolute path under UPLOADS_PATH (development only)
    """
    filename = _new_filename(original_name, patient_name)
    try:
        if STORAGE_BACKEND == "gcs":
            object_name = f"uploads/{filename}"
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            _get_bucket().blob(object_name).upload_from_string(file_bytes, content_type=content_type)
            return object_name

        Path(UPLOADS_PATH).mkdir(parents=True, exist_ok=True)
        target_path = Path(UPLOADS_PATH) / filename
        target_path.write_bytes(file_bytes)
        return str(target_path)
    except Exception as error:  # noqa: BLE001 - surface any storage failure uniformly
        raise StorageError(f"Could not store upload: {error}") from error


def load_image_bytes(image_path: str) -> Optional[bytes]:
    """Return the stored image bytes, or None if it does not exist."""
    try:
        if STORAGE_BACKEND == "gcs":
            from google.api_core.exceptions import NotFound

            if not image_path.startswith("uploads/") or ".." in image_path:
                return None
            try:
                return _get_bucket().blob(image_path).download_as_bytes()
            except NotFound:
                return None

        upload_root = Path(UPLOADS_PATH).resolve()
        path = Path(image_path).resolve()
        if upload_root not in path.parents or not path.is_file():
            return None
        return path.read_bytes()
    except Exception as error:  # noqa: BLE001
        raise StorageError(f"Could not read upload: {error}") from error
