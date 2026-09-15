from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.core.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine_kwargs = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def ensure_study_columns() -> None:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE studies ADD COLUMN IF NOT EXISTS patient_name VARCHAR(255)"))
        connection.execute(text("ALTER TABLE studies ADD COLUMN IF NOT EXISTS prediction_results JSONB"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
