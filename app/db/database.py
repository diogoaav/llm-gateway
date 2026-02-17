"""Database connection and session management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def get_database_url() -> str:
    """Get database URL from environment. Use SQLite if DATABASE_URL not set."""
    url = os.getenv("DATABASE_URL")
    if url:
        # Handle Heroku/DO postgres URL (postgres:// -> postgresql://)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return "sqlite:///./llm_gateway.db"


database_url = get_database_url()
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    poolclass=StaticPool if database_url.startswith("sqlite") else None,
    echo=os.getenv("SQL_ECHO", "").lower() == "true",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables."""
    from app.db import models  # noqa: F401 - register models with Base
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
