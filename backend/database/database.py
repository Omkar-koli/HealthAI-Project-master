from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.core.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine_kwargs = {"future": True, "pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Several replicas share one small Cloud SQL instance with a low connection limit, so each pod
    # keeps a small pool (default max 5 connections per pod) and fails fast instead of hanging.
    engine_kwargs["connect_args"] = {"connect_timeout": 3}
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "3"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "2"))
    engine_kwargs["pool_timeout"] = 10

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
