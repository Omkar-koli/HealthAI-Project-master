from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError

from backend.database.database import Base, SessionLocal, engine, ensure_study_columns
from backend.database.models import Study
from backend.database.studies import complete_study, create_study, fail_study, recent_studies
from backend.core.config import UPLOADS_PATH
from backend.inference import analyze_image
from backend.services.storage import save_uploaded_image

Base.metadata.create_all(bind=engine)
ensure_study_columns()

app = FastAPI(title="HealthAI Milestone 1 API")
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
    return {"status": "ok"}


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
        stored_path = save_uploaded_image(
            image_bytes,
            file.filename or "upload.png",
            patient_name,
        )
        study = create_study(
            db,
            patient_name,
            file.filename or Path(stored_path).name,
            stored_path,
        )

        try:
            predictions = analyze_image(stored_path)
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
def get_study_image(study_id: int) -> FileResponse:
    db = SessionLocal()
    try:
        study = db.get(Study, study_id)
        if study is None:
            raise HTTPException(status_code=404, detail="Study not found.")
        upload_root = Path(UPLOADS_PATH).resolve()
        image_path = Path(study.image_path).resolve()
        if upload_root.resolve() not in image_path.parents or not image_path.is_file():
            raise HTTPException(status_code=404, detail="Study image not found.")
        return FileResponse(image_path, filename=study.image_name)
    finally:
        db.close()
