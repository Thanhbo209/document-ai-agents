from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent
from tests.test_reviews_api import create_review_item, create_workspace


def test_export_review_items_json_includes_evidence(
    client: TestClient,
    db_session: Session,
) -> None:
    _user_id, workspace_id, headers = create_workspace(db_session)
    create_review_item(client, workspace_id, headers)

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/exports/review-items",
        headers=headers,
        params={"format": "json"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["evidence"]["source_id"] == "S1"

    events = list(db_session.scalars(select(AuditEvent)).all())
    assert events[-1].event_type == "export.review_items"


def test_export_review_items_csv_includes_citation_data(
    client: TestClient,
    db_session: Session,
) -> None:
    _user_id, workspace_id, headers = create_workspace(db_session)
    create_review_item(client, workspace_id, headers)

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/exports/review-items",
        headers=headers,
        params={"format": "csv"},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "renewal_date" in response.text
    assert "Renewal date" in response.text
