from sqlalchemy import select

from app.auth.security import hash_password
from app.db.models import User, Workspace
from app.db.session import SessionLocal
from app.repositories.workspaces import WorkspaceRepository


def main() -> None:
    db = SessionLocal()

    try:
        repo = WorkspaceRepository(db)

        user = db.scalar(select(User).where(User.email == "dev@example.com"))

        if user is None:
            user = repo.create_user(
                email="dev@example.com",
                display_name="Dev User",
                password_hash=hash_password("password123"),
            )
        elif user.password_hash is None:
            user.password_hash = hash_password("password123")

        workspace = db.scalar(
            select(Workspace).where(
                Workspace.owner_user_id == user.id,
                Workspace.name == "Dev Workspace",
            )
        )

        if workspace is None:
            workspace = repo.create_workspace(
                name="Dev Workspace",
                owner_user_id=user.id,
            )

        db.commit()

        print("email: dev@example.com")
        print("password: password123")
        print("user_id:", user.id)
        print("workspace_id:", workspace.id)

    finally:
        db.close()


if __name__ == "__main__":
    main()
