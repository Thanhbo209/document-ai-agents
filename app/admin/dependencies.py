from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.db.models import User


def require_platform_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required.",
        )

    return current_user
