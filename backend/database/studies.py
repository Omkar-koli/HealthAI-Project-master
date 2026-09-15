from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import Study


def create_study(db: Session, patient_name: str, image_name: str, image_path: str) -> Study:
    study = Study(
        patient_name=patient_name,
        image_name=image_name,
        image_path=image_path,
        status="processing",
    )
    db.add(study)
    db.commit()
    db.refresh(study)
    return study


def complete_study(
    db: Session,
    study: Study,
    predicted_condition: str,
    confidence: float,
    prediction_results: dict[str, float],
) -> Study:
    study.status = "completed"
    study.predicted_condition = predicted_condition
    study.confidence = confidence
    study.prediction_results = prediction_results
    db.commit()
    db.refresh(study)
    return study


def fail_study(db: Session, study: Study) -> None:
    study.status = "failed"
    db.commit()


def recent_studies(db: Session, limit: int = 10) -> list[Study]:
    statement = select(Study).order_by(Study.created_at.desc()).limit(max(1, min(limit, 100)))
    return list(db.scalars(statement).all())
