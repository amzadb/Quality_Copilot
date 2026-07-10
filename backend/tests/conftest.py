"""Shared pytest fixtures for the Quality Copilot backend."""

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.models import Base


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Session:
    session_factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def migrated_db_path(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    database_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    from app.config import settings

    settings.database_url = database_url

    from app.models import base as db_base

    db_base.engine.dispose()
    db_base.engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    db_base.SessionLocal.configure(bind=db_base.engine)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")

    inspector = inspect(db_base.engine)
    return database_url, inspector
