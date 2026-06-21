import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token, hash_password
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.repositories.workspaces import WorkspaceRepository
from app.services.vector_runtime import get_runtime_embedder, get_runtime_vector_store


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
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

    db = testing_session_local()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        get_runtime_embedder.cache_clear()
        get_runtime_vector_store.cache_clear()


@pytest.fixture
def client(
    db_session: Session,
    tmp_path,
) -> TestClient:
    settings = get_settings()
    settings.upload_dir = str(tmp_path / "uploads")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(db_session: Session) -> dict[str, str]:
    repo = WorkspaceRepository(db_session)
    user = repo.create_user(
        email="auth-user@example.com",
        display_name="Auth User",
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name="Auth Workspace",
        owner_user_id=user.id,
    )
    db_session.commit()

    token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return {
        "Authorization": f"Bearer {token}",
        "X-Test-Workspace-Id": workspace.id,
    }
