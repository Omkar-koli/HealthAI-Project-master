from __future__ import annotations

import io
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError

from backend.core.config import APP_ENV, DATABASE_MODE, STORAGE_BACKEND
from backend.database.database import SessionLocal
from backend.database.models import Study
from backend.database.studies import complete_study, create_study, fail_study, recent_studies
from backend.inference import analyze_image
from backend.services.storage import StorageError, load_image_bytes, save_uploaded_image

# NOTE: tables are no longer created here. The schema comes from migrations/*.sql.

app = FastAPI(title="HealthAI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def study_response(study: Study, predictions: dict[str, float] | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "study_id": study.id,
        "patient_name": study.patient_name,
        "image_name": study.image_name,
        "status": study.status,
        "predicted_condition": study.predicted_condition,
        "confidence": study.confidence,
        "prediction_results": study.prediction_results or predictions or {},
        "image_url": f"/studies/{study.id}/image",
        "created_at": study.created_at.isoformat() if study.created_at else None,
    }
    if predictions is not None:
        response["predictions"] = predictions
    return response


@app.get("/health")
def health() -> dict[str, str]:
    # environment/database/storage make it obvious which stack you are looking at
    # (cloud vs. a local dev stack), so screenshots and demos are never ambiguous.
    return {
        "status": "ok",
        "environment": APP_ENV,
        "database": DATABASE_MODE,
        "storage": STORAGE_BACKEND,
    }


@app.post("/studies/analyze")
async def analyze_study(
    patient_name: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    patient_name = patient_name.strip()
    if not patient_name:
        raise HTTPException(status_code=400, detail="Patient name is required.")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, and PNG files are accepted.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        Image.open(io.BytesIO(image_bytes)).verify()
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.") from error

    db = SessionLocal()
    study = None
    try:
        try:
            stored_path = save_uploaded_image(
                image_bytes,
                file.filename or "upload.png",
                patient_name,
            )
        except StorageError as error:
            raise HTTPException(status_code=503, detail="Image storage failed.") from error

        study = create_study(
            db,
            patient_name,
            file.filename or Path(stored_path).name,
            stored_path,
        )

        try:
            # Inference runs on the bytes already in memory: no local file is re-read.
            predictions = analyze_image(image_bytes)
            if not predictions:
                raise RuntimeError("No configured CheXpert findings were returned.")
            predicted_condition, confidence = max(predictions.items(), key=lambda item: item[1])
            complete_study(db, study, predicted_condition, confidence, predictions)
            return study_response(study, predictions)
        except Exception as error:
            fail_study(db, study)
            raise HTTPException(status_code=500, detail="Model inference failed.") from error
    except SQLAlchemyError as error:
        db.rollback()
        if study is not None:
            try:
                fail_study(db, study)
            except SQLAlchemyError:
                db.rollback()
        raise HTTPException(status_code=503, detail="Database operation failed.") from error
    finally:
        db.close()


@app.get("/studies/recent")
def get_recent_studies(limit: int = 10) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        return [study_response(study) for study in recent_studies(db, limit)]
    finally:
        db.close()


@app.get("/studies/{study_id}")
def get_study(study_id: int) -> dict[str, Any]:
    db = SessionLocal()
    try:
        study = db.get(Study, study_id)
        if study is None:
            raise HTTPException(status_code=404, detail="Study not found.")
        return study_response(study)
    finally:
        db.close()


@app.get("/studies/{study_id}/image")
def get_study_image(study_id: int) -> Response:
    db = SessionLocal()
    try:
        study = db.get(Study, study_id)
        if study is None:
            raise HTTPException(status_code=404, detail="Study not found.")
        image_name, image_path = study.image_name, study.image_path
    finally:
        db.close()

    try:
        image_bytes = load_image_bytes(image_path)
    except StorageError as error:
        raise HTTPException(status_code=503, detail="Image storage unavailable.") from error
    if image_bytes is None:
        raise HTTPException(status_code=404, detail="Study image not found.")

    media_type = mimetypes.guess_type(image_name)[0] or "application/octet-stream"
    return Response(
        content=image_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(image_name)}"},
    )
