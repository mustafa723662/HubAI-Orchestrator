from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_database_url

# backend/app/db/database.py -> parents[2] == backend/
BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_URL = f"sqlite:///{BASE_DIR / 'hubai.db'}"

DATABASE_URL = get_database_url() or DEFAULT_SQLITE_URL

# check_same_thread is a SQLite-only pysqlite option; other drivers (e.g.
# psycopg for Postgres) reject unknown connect_args.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
