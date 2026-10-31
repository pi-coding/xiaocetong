from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import BASE_DIR, settings


def _normalize_url(url: str) -> str:
    prefix = "sqlite:///"
    if url.startswith(prefix) and not url.startswith("sqlite:////"):
        raw = url[len(prefix):]
        if raw and not raw.startswith(":memory:") and not Path(raw).is_absolute():
            return f"sqlite:///{(BASE_DIR / raw).as_posix()}"
    return url


DATABASE_URL = _normalize_url(settings.database_url)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)