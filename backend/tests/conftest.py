"""Shared pytest fixtures for the Quality Copilot backend."""

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, TypeVar

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.credential_store import reset_credential_store
from app.main import app
from app.models import Base
from app.schemas.settings import (
    GitProviderSettings,
    JiraSettings,
    LLMSettings,
    SettingsUpdate,
    TestRailSettings,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]


T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run async integration code under plain pytest (no pytest-asyncio required)."""
    return asyncio.run(coro)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def credentials_file(tmp_path, monkeypatch):
    path = tmp_path / "credentials.json"
    monkeypatch.setattr(settings, "credentials_path", str(path))
    store = reset_credential_store(path)
    yield store


@pytest.fixture
def configured_credentials(credentials_file, monkeypatch):
    monkeypatch.setattr(settings, "jira_email", "qa@example.com")
    credentials_file.merge_update(
        SettingsUpdate(
            jira=JiraSettings(base_url="acme.atlassian.net", token="jira-token"),
            git_provider=GitProviderSettings(
                type="bitbucket",
                workspace="acme",
                username="qa-bot",
                token="git-app-password",
            ),
            testrail=TestRailSettings(
                base_url="acme.testrail.io",
                username="qa@example.com",
                token="testrail-token",
            ),
            llm=LLMSettings(provider="claude", token="llm-token"),
        )
    )
    return credentials_file


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
    settings.database_url = database_url

    from app.models import base as db_base

    db_base.engine.dispose()
    db_base.engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    db_base.SessionLocal.configure(bind=db_base.engine)

    alembic_cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")

    inspector = inspect(db_base.engine)
    return database_url, inspector
