from sqlalchemy.orm import Session

from app.embeddings.embedder import HashEmbedder
from app.indexing.indexer import DocumentIndexer
from app.repositories.documents import DocumentRepository
from app.repositories.workspaces import WorkspaceRepository
from app.storage.collections import workspace_collection_name
from app.storage.memory_vector_store import InMemoryVectorStore


def create_document_with_chunks(db_session: Session) -> tuple[str, str]:
    workspace_repo = WorkspaceRepository(db_session)
    document_repo = DocumentRepository(db_session)

    user = workspace_repo.create_user(
        email="indexer@example.com",
        display_name="Indexer",
    )
    workspace = workspace_repo.create_workspace(
        name="Indexer Workspace",
        owner_user_id=user.id,
    )
    document = document_repo.create_document(
        workspace_id=workspace.id,
        title="Indexer Test Document",
        source_type="text",
    )

    document_repo.add_chunk(
        workspace_id=workspace.id,
        document_id=document.id,
        chunk_index=0,
        text="First chunk text.",
        source_page=None,
        source_start_offset=0,
        source_end_offset=17,
        token_count=4,
        source_metadata={"filename": "notes.txt"},
    )
    document_repo.add_chunk(
        workspace_id=workspace.id,
        document_id=document.id,
        chunk_index=1,
        text="Second chunk text.",
        source_page=None,
        source_start_offset=18,
        source_end_offset=36,
        token_count=4,
        source_metadata={"filename": "notes.txt"},
    )

    db_session.commit()

    return workspace.id, document.id


def test_document_indexer_indexes_chunks_into_workspace_collection(
    db_session: Session,
) -> None:
    workspace_id, document_id = create_document_with_chunks(db_session)
    vector_store = InMemoryVectorStore()
    indexer = DocumentIndexer(
        db=db_session,
        embedder=HashEmbedder(),
        vector_store=vector_store,
    )

    result = indexer.index_document(
        workspace_id=workspace_id,
        document_id=document_id,
    )

    collection_name = workspace_collection_name(workspace_id)
    records = vector_store.list_records(collection_name)

    assert result.collection_name == collection_name
    assert result.chunks_indexed == 2
    assert result.embedding_model_name == "hash-embedder"
    assert result.embedding_model_version == "hash-embedder-v1"

    assert len(records) == 2
    assert records[0].metadata["workspace_id"] == workspace_id
    assert records[0].metadata["document_id"] == document_id
    assert records[0].metadata["embedding_model_version"] == "hash-embedder-v1"


def test_document_indexing_is_idempotent(
    db_session: Session,
) -> None:
    workspace_id, document_id = create_document_with_chunks(db_session)
    vector_store = InMemoryVectorStore()
    indexer = DocumentIndexer(
        db=db_session,
        embedder=HashEmbedder(),
        vector_store=vector_store,
    )

    indexer.index_document(workspace_id=workspace_id, document_id=document_id)
    indexer.index_document(workspace_id=workspace_id, document_id=document_id)

    records = vector_store.list_records(workspace_collection_name(workspace_id))

    assert len(records) == 2


def test_document_can_be_reembedded_after_chunk_change(
    db_session: Session,
) -> None:
    workspace_id, document_id = create_document_with_chunks(db_session)
    vector_store = InMemoryVectorStore()
    indexer = DocumentIndexer(
        db=db_session,
        embedder=HashEmbedder(),
        vector_store=vector_store,
    )

    indexer.index_document(workspace_id=workspace_id, document_id=document_id)

    document_repo = DocumentRepository(db_session)
    document_repo.add_chunk(
        workspace_id=workspace_id,
        document_id=document_id,
        chunk_index=2,
        text="Third chunk text.",
        source_page=None,
        source_start_offset=37,
        source_end_offset=54,
        token_count=4,
        source_metadata={"filename": "notes.txt"},
    )
    db_session.commit()

    indexer.index_document(workspace_id=workspace_id, document_id=document_id)

    records = vector_store.list_records(workspace_collection_name(workspace_id))

    assert len(records) == 3
