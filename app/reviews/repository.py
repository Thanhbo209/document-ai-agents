from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.db.models import ReviewItem


class ReviewItemNotFoundError(ValueError):
    pass


class InvalidReviewTransitionError(ValueError):
    pass


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_repo = AuditEventRepository(db)

    def create_review_item(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        field_name: str | None,
        original_value: dict[str, Any] | None,
        evidence: dict[str, Any],
        actor_user_id: str | None = None,
    ) -> ReviewItem:
        item = ReviewItem(
            workspace_id=workspace_id,
            target_type=target_type,
            target_id=target_id,
            field_name=field_name,
            original_value=original_value,
            reviewed_value=None,
            evidence=evidence,
            status="pending",
        )
        self.db.add(item)
        self.db.flush()

        self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type="review_item.created",
            entity_type="review_item",
            entity_id=item.id,
            payload={
                "target_type": target_type,
                "target_id": target_id,
                "field_name": field_name,
            },
        )

        return item

    def list_review_items(
        self,
        workspace_id: str,
        status: str | None = None,
    ) -> list[ReviewItem]:
        statement = select(ReviewItem).where(ReviewItem.workspace_id == workspace_id)

        if status:
            statement = statement.where(ReviewItem.status == status)

        statement = statement.order_by(ReviewItem.created_at.desc())

        return list(self.db.scalars(statement).all())

    def get_review_item(
        self,
        workspace_id: str,
        review_item_id: str,
    ) -> ReviewItem:
        item = self.db.get(ReviewItem, review_item_id)

        if item is None or item.workspace_id != workspace_id:
            raise ReviewItemNotFoundError("Review item not found.")

        return item

    def approve_review_item(
        self,
        workspace_id: str,
        review_item_id: str,
        reviewer_user_id: str | None,
        reviewed_value: dict[str, Any] | None = None,
        comments: str | None = None,
    ) -> ReviewItem:
        item = self.get_review_item(workspace_id, review_item_id)

        if item.status != "pending":
            raise InvalidReviewTransitionError("Only pending review items can be approved.")

        item.status = "approved"
        item.reviewed_value = reviewed_value or item.original_value
        item.reviewer_user_id = reviewer_user_id
        item.reviewed_at = datetime.now(UTC)
        item.comments = comments

        self.db.flush()

        self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=reviewer_user_id,
            event_type="review_item.approved",
            entity_type="review_item",
            entity_id=item.id,
            payload={
                "field_name": item.field_name,
                "reviewed_value": item.reviewed_value,
                "comments": comments,
            },
        )

        return item

    def reject_review_item(
        self,
        workspace_id: str,
        review_item_id: str,
        reviewer_user_id: str | None,
        comments: str | None = None,
    ) -> ReviewItem:
        item = self.get_review_item(workspace_id, review_item_id)

        if item.status != "pending":
            raise InvalidReviewTransitionError("Only pending review items can be rejected.")

        item.status = "rejected"
        item.reviewer_user_id = reviewer_user_id
        item.reviewed_at = datetime.now(UTC)
        item.comments = comments

        self.db.flush()

        self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=reviewer_user_id,
            event_type="review_item.rejected",
            entity_type="review_item",
            entity_id=item.id,
            payload={
                "field_name": item.field_name,
                "comments": comments,
            },
        )

        return item
