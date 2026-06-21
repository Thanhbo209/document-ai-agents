from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.models.enums import WorkspaceRole
from app.repositories.workspaces import WorkspaceRepository

router = APIRouter(tags=["auth"])


class AuthWorkspaceResponse(BaseModel):
    id: str
    name: str
    role: str


class AuthUserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None
    workspaces: list[AuthWorkspaceResponse]


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
    default_workspace_id: str | None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None
    workspace_name: str = "My Workspace"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    repo = WorkspaceRepository(db)
    existing_user = repo.get_user_by_email(request.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    user = repo.create_user(
        email=request.email,
        display_name=request.display_name,
        password_hash=hash_password(request.password),
    )
    workspace = repo.create_workspace(
        name=request.workspace_name,
        owner_user_id=user.id,
    )

    AuditEventRepository(db).record_event(
        workspace_id=workspace.id,
        actor_user_id=user.id,
        event_type="auth.registered",
        entity_type="user",
        entity_id=user.id,
        payload={"email": user.email},
    )

    db.commit()

    return _auth_response(db=db, user=user, default_workspace_id=workspace.id)


@router.post("/auth/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    repo = WorkspaceRepository(db)
    user = repo.get_user_by_email(request.email)

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    workspaces = repo.list_workspaces_for_user(user.id)
    default_workspace_id = workspaces[0].id if workspaces else None

    if default_workspace_id is not None:
        AuditEventRepository(db).record_event(
            workspace_id=default_workspace_id,
            actor_user_id=user.id,
            event_type="auth.login",
            entity_type="user",
            entity_id=user.id,
            payload={"email": user.email},
        )
        db.commit()

    return _auth_response(
        db=db,
        user=user,
        default_workspace_id=default_workspace_id,
    )


@router.get("/auth/me", response_model=AuthUserResponse)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthUserResponse:
    return _user_response(db=db, user=current_user)


def _auth_response(
    db: Session,
    user: User,
    default_workspace_id: str | None,
) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(
            user_id=user.id,
            email=user.email,
        ),
        user=_user_response(db=db, user=user),
        default_workspace_id=default_workspace_id,
    )


def _user_response(db: Session, user: User) -> AuthUserResponse:
    repo = WorkspaceRepository(db)
    workspaces = repo.list_workspaces_for_user(user.id)

    memberships = {membership.workspace_id: membership.role for membership in user.memberships}

    return AuthUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        workspaces=[
            AuthWorkspaceResponse(
                id=workspace.id,
                name=workspace.name,
                role=memberships.get(workspace.id, WorkspaceRole.MEMBER.value),
            )
            for workspace in workspaces
        ],
    )
