from sqlalchemy.orm import Session

from app.repositories.documents import DocumentRepository
from app.repositories.workspaces import WorkspaceRepository


def test_documents_are_scoped_by_workspace(db_session: Session) -> None:
    workspace_repo = WorkspaceRepository(db_session)
    document_repo = DocumentRepository(db_session)

    user_a = workspace_repo.create_user(
        email="user-a@example.com",
        display_name="User A",
    )
    user_b = workspace_repo.create_user(
        email="user-b@example.com",
        display_name="User B",
    )

    workspace_a = workspace_repo.create_workspace(
        name="Workspace A",
        owner_user_id=user_a.id,
    )
    workspace_b = workspace_repo.create_workspace(
        name="Workspace B",
        owner_user_id=user_b.id,
    )

    document_a = document_repo.create_document(
        workspace_id=workspace_a.id,
        title="A private document",
        source_type="pdf",
    )
    document_b = document_repo.create_document(
        workspace_id=workspace_b.id,
        title="B private document",
        source_type="pdf",
    )

    visible_to_workspace_a = document_repo.list_documents_for_workspace(workspace_a.id)

    assert [document.id for document in visible_to_workspace_a] == [document_a.id]

    assert document_repo.get_document_for_workspace(document_a.id, workspace_a.id) is not None
    assert document_repo.get_document_for_workspace(document_a.id, workspace_b.id) is None
    assert document_repo.get_document_for_workspace(document_b.id, workspace_a.id) is None


def test_chunks_are_scoped_by_workspace_and_document(db_session: Session) -> None:
    workspace_repo = WorkspaceRepository(db_session)
    document_repo = DocumentRepository(db_session)

    user = workspace_repo.create_user(
        email="owner@example.com",
        display_name="Owner",
    )
    workspace = workspace_repo.create_workspace(
        name="Research Workspace",
        owner_user_id=user.id,
    )
    document = document_repo.create_document(
        workspace_id=workspace.id,
        title="Research Paper",
        source_type="pdf",
    )

    document_repo.add_chunk(
        workspace_id=workspace.id,
        document_id=document.id,
        chunk_index=0,
        text="This is the first extracted chunk.",
        source_page=1,
        token_count=7,
        source_metadata={"section": "Introduction"},
    )

    chunks = document_repo.list_chunks_for_document(
        workspace_id=workspace.id,
        document_id=document.id,
    )

    assert len(chunks) == 1
    assert chunks[0].text == "This is the first extracted chunk."
    assert chunks[0].source_page == 1
    assert chunks[0].source_metadata == {"section": "Introduction"}


def test_user_can_only_access_joined_workspace(db_session: Session) -> None:
    workspace_repo = WorkspaceRepository(db_session)

    user_a = workspace_repo.create_user(email="a@example.com")
    user_b = workspace_repo.create_user(email="b@example.com")

    workspace_a = workspace_repo.create_workspace(
        name="Workspace A",
        owner_user_id=user_a.id,
    )

    assert workspace_repo.get_workspace_for_user(workspace_a.id, user_a.id) is not None
    assert workspace_repo.get_workspace_for_user(workspace_a.id, user_b.id) is None
