from app.auth.security import hash_password
from app.db.models import User
from app.db.session import SessionLocal
from app.repositories.workspaces import WorkspaceRepository

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "password123"


def main() -> None:
    db = SessionLocal()

    try:
        repo = WorkspaceRepository(db)
        user = repo.get_user_by_email(ADMIN_EMAIL)

        if user is None:
            user = User(
                email=ADMIN_EMAIL,
                display_name="Platform Admin",
            )
            db.add(user)
            db.flush()
        else:
            user.display_name = user.display_name or "Platform Admin"

        user.password_hash = hash_password(ADMIN_PASSWORD)
        user.is_platform_admin = True
        db.commit()

        print("Platform admin user is ready.")
        print(f"Email: {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
