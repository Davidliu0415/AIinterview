from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base, Setting


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=3600, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def ensure_database_exists() -> None:
    server_engine = create_engine(settings.mysql_server_url, pool_pre_ping=True, future=True)
    try:
        with server_engine.begin() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        server_engine.dispose()


def seed_settings(db: Session) -> None:
    defaults = {
        "deepseek_model": settings.deepseek_model,
        "deepseek_temperature": str(settings.deepseek_temperature),
        "speech_language": settings.speech_language,
        "max_interview_questions": str(settings.max_interview_questions),
    }
    for key, value in defaults.items():
        existing = db.query(Setting).filter(Setting.key == key).one_or_none()
        if existing is None:
            db.add(Setting(key=key, value=value))
    db.commit()


def init_db() -> None:
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_settings(db)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
