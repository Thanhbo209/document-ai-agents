from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import Workspace
from app.db.session import get_db
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.permissions.policies import WorkspacePermission
from app.reviews.repository import (
    InvalidReviewTransitionError,
    ReviewItemNotFoundError,
    ReviewRepository,
)

router = APIRouter(tags=["reviews"])

create_reviews_access = require_workspace_permission(WorkspacePermission.CREATE_REVIEWS)

read_reviews_access = require_workspace_permission(WorkspacePermission.READ_REVIEWS)

decide_reviews_access = require_workspace_permission(WorkspacePermission.DECIDE_REVIEWS)


class CreateReviewItemRequest(BaseModel):
    target_type: str
    target_id: str
    field_name: str | None = None
    original_value: dict[str, Any] | None = None
    evidence: dict[str, Any]
    actor_user_id: str | None = None


class ReviewDecisionRequest(BaseModel):
    reviewer_user_id: str | None = None
    reviewed_value: dict[str, Any] | None = None
    comments: str | None = None


class ReviewItemResponse(BaseModel):
    id: str
    workspace_id: str
    target_type: str
    target_id: str
    field_name: str | None
    original_value: dict[str, Any] | None
    reviewed_value: dict[str, Any] | None
    evidence: dict[str, Any]
    status: str
    reviewer_user_id: str | None
    reviewed_at: datetime | None
    comments: str | None
    created_at: datetime
    updated_at: datetime


@router.post(
    "/workspaces/{workspace_id}/review-items",
    response_model=ReviewItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review_item(
    workspace_id: str,
    request: CreateReviewItemRequest,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(create_reviews_access),
) -> ReviewItemResponse:
    _ensure_workspace_exists(db, workspace_id)

    repo = ReviewRepository(db)
    item = repo.create_review_item(
        workspace_id=workspace_id,
        target_type=request.target_type,
        target_id=request.target_id,
        field_name=request.field_name,
        original_value=request.original_value,
        evidence=request.evidence,
        actor_user_id=request.actor_user_id,
    )
    db.commit()

    return _review_item_response(item)


@router.get(
    "/workspaces/{workspace_id}/review-items",
    response_model=list[ReviewItemResponse],
)
def list_review_items(
    workspace_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(read_reviews_access),
) -> list[ReviewItemResponse]:
    _ensure_workspace_exists(db, workspace_id)

    repo = ReviewRepository(db)
    items = repo.list_review_items(
        workspace_id=workspace_id,
        status=status_filter,
    )

    return [_review_item_response(item) for item in items]


@router.post(
    "/workspaces/{workspace_id}/review-items/{review_item_id}/approve",
    response_model=ReviewItemResponse,
)
def approve_review_item(
    workspace_id: str,
    review_item_id: str,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(decide_reviews_access),
) -> ReviewItemResponse:
    _ensure_workspace_exists(db, workspace_id)

    repo = ReviewRepository(db)

    try:
        item = repo.approve_review_item(
            workspace_id=workspace_id,
            review_item_id=review_item_id,
            reviewer_user_id=request.reviewer_user_id or access.user.id,
            reviewed_value=request.reviewed_value,
            comments=request.comments,
        )
    except ReviewItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidReviewTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    db.commit()

    return _review_item_response(item)


@router.post(
    "/workspaces/{workspace_id}/review-items/{review_item_id}/reject",
    response_model=ReviewItemResponse,
)
def reject_review_item(
    workspace_id: str,
    review_item_id: str,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(decide_reviews_access),
) -> ReviewItemResponse:
    _ensure_workspace_exists(db, workspace_id)

    repo = ReviewRepository(db)

    try:
        item = repo.reject_review_item(
            workspace_id=workspace_id,
            review_item_id=review_item_id,
            reviewer_user_id=request.reviewer_user_id,
            comments=request.comments,
        )
    except ReviewItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidReviewTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    db.commit()

    return _review_item_response(item)


def _ensure_workspace_exists(db: Session, workspace_id: str) -> None:
    if db.get(Workspace, workspace_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )


def _review_item_response(item) -> ReviewItemResponse:
    return ReviewItemResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        target_type=item.target_type,
        target_id=item.target_id,
        field_name=item.field_name,
        original_value=item.original_value,
        reviewed_value=item.reviewed_value,
        evidence=item.evidence,
        status=item.status,
        reviewer_user_id=item.reviewer_user_id,
        reviewed_at=item.reviewed_at,
        comments=item.comments,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
