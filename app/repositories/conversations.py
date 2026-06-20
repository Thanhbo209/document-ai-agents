from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Citation, ConversationMessage
from app.models.enums import MessageRole


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_message(
        self,
        workspace_id: str,
        role: MessageRole,
        content: str,
        user_id: str | None = None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role.value,
            content=content,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def create_citation(
        self,
        message_id: str,
        chunk_id: str,
        rank: int,
        relevance_score: float | None,
        quote: str | None,
    ) -> Citation:
        citation = Citation(
            message_id=message_id,
            chunk_id=chunk_id,
            rank=rank,
            relevance_score=relevance_score,
            quote=quote,
        )
        self.db.add(citation)
        self.db.flush()
        return citation

    def list_messages_for_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
    ) -> list[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.workspace_id == workspace_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )

        return list(reversed(self.db.scalars(statement).all()))
