from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.routes.upload import get_file_storage
from app.storage.local import LocalFileStorage


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    with testing_session_local() as session:
        yield session

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session, tmp_path: Path) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    def override_get_file_storage() -> LocalFileStorage:
        return LocalFileStorage(tmp_path / "uploads")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_file_storage] = override_get_file_storage

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
