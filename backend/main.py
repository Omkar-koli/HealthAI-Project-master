from __future__ import annotations

import io
import json
import logging
import mimetypes
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.core.config import APP_ENV, APP_VERSION, DATABASE_MODE, STORAGE_BACKEND
from backend.database.database import SessionLocal
from backend.database.models import Study
from backend.database.studies import complete_study, create_study, fail_study, recent_studies
from backend.inference import analyze_image, warm_up
from backend.services.storage import StorageError, load_image_bytes, save_uploaded_image

# NOTE: tables are no longer created here. The schema comes from migrations/*.sql.

logger = logging.getLogger("uvicorn.error")


# ---------------------------------------------------------------------------
# Structured (JSON) request logging — Milestone 6.
#
# Each line written to stdout is one JSON object. GKE's logging agent parses
# JSON lines from container stdout automatically, so these show up in Cloud
# Logging as structured entries (jsonPayload) rather than plain text, which is
# what the log-based metric in Phase 3 filters on (jsonPayload.status >= 500).
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
        }
        for field in ("method", "path", "status", "duration_ms", "version"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload)


request_logger = logging.getLogger("healthai.request")
request_logger.setLevel(logging.INFO)
request_logger.propagate = False
if not request_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(JsonFormatter())
    request_logger.addHandler(_handler)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the model before the server accepts traffic. In dev/tests without a model file, carry on.
    try:
        warm_up()
        logger.info("Model warmed up.")
    except Exception as error:  # noqa: BLE001
        logger.warning("Model warm-up skipped: %s", error)
    yield


app = FastAPI(title="HealthAI API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Write one JSON log line per request, with a numeric status field.

    This is what the log-based metric (Phase 3) will filter on to count 5xx
    responses, and what the demo shows in Logs Explorer next to the triggered
    test error.
    """
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    if response.status_code >= 500:
        level = logging.ERROR
    elif response.status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO

    request_logger.log(
        level,
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "version": APP_VERSION,
        },
    )
    return response


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
        "version": APP_VERSION,
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """LIVENESS probe: the process is up and can answer HTTP.

    It deliberately checks NO dependencies. If it called the database, a database outage would make
    Kubernetes restart perfectly healthy pods and turn a small problem into a bigger one.
    """
    return {"status": "alive"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    """READINESS probe: can this pod serve real traffic right now? Checks the database.

    Failing this does not restart the pod; it only removes it from the load balancer until the
    database answers again.
    """
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="Database not reachable.") from error
    finally:
        db.close()
    return {"status": "ready", "database": "ok"}


@app.get("/debug/error")
def debug_error() -> dict[str, str]:
    """Deliberately returns a 500 so the Milestone 6 demo has a controlled error to show:
    this request's JSON log entry (status=500, severity=ERROR), the matching rise in the
    log-based metric, the alert, and the dashboard spike.

    Not used by real patients — it is only reachable through the diagnostics button in the
    Streamlit dashboard, since the backend itself has no public DNS name of its own.
    """
    raise HTTPException(status_code=500, detail="Deliberate test error for the monitoring demo.")


@app.post("/studies/analyze")
def analyze_study(
    patient_name: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    patient_name = patient_name.strip()
    if not patient_name:
        raise HTTPException(status_code=400, detail="Patient name is required.")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, and PNG files are accepted.")

    image_bytes = file.file.read()
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
