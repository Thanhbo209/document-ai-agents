import csv
import json
from io import StringIO

from app.db.models import ReviewItem


def export_review_items_json(items: list[ReviewItem]) -> str:
    payload = [
        {
            "id": item.id,
            "workspace_id": item.workspace_id,
            "target_type": item.target_type,
            "target_id": item.target_id,
            "field_name": item.field_name,
            "original_value": item.original_value,
            "reviewed_value": item.reviewed_value,
            "evidence": item.evidence,
            "status": item.status,
            "reviewer_user_id": item.reviewer_user_id,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
            "comments": item.comments,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in items
    ]

    return json.dumps(payload, indent=2)


def export_review_items_csv(items: list[ReviewItem]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "target_type",
            "target_id",
            "field_name",
            "status",
            "original_value",
            "reviewed_value",
            "evidence",
            "reviewer_user_id",
            "reviewed_at",
            "comments",
        ],
    )
    writer.writeheader()

    for item in items:
        writer.writerow(
            {
                "id": item.id,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "field_name": item.field_name or "",
                "status": item.status,
                "original_value": json.dumps(item.original_value),
                "reviewed_value": json.dumps(item.reviewed_value),
                "evidence": json.dumps(item.evidence),
                "reviewer_user_id": item.reviewer_user_id or "",
                "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else "",
                "comments": item.comments or "",
            }
        )

    return output.getvalue()
