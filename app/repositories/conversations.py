from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Citation, ConversationMessage, ConversationSession, utc_now
from app.models.enums import MessageRole


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(
        self,
        workspace_id: str,
        user_id: str | None,
        title: str = "New chat",
    ) -> ConversationSession:
        session = ConversationSession(
            workspace_id=workspace_id,
            user_id=user_id,
            title=_clean_title(title),
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_session(
        self,
        workspace_id: str,
        session_id: str,
    ) -> ConversationSession | None:
        return self.db.scalar(
            select(ConversationSession).where(
                ConversationSession.workspace_id == workspace_id,
                ConversationSession.id == session_id,
            )
        )

    def list_sessions_for_workspace(
        self,
        workspace_id: str,
    ) -> list[tuple[ConversationSession, int]]:
        statement = (
            select(ConversationSession, func.count(ConversationMessage.id))
            .outerjoin(
                ConversationMessage,
                ConversationMessage.session_id == ConversationSession.id,
            )
            .where(ConversationSession.workspace_id == workspace_id)
            .group_by(ConversationSession.id)
            .order_by(ConversationSession.updated_at.desc())
        )
        return list(self.db.execute(statement).all())

    def rename_session(
        self,
        session: ConversationSession,
        title: str,
    ) -> ConversationSession:
        session.title = _clean_title(title)
        self.db.flush()
        return session

    def touch_session(self, session: ConversationSession) -> ConversationSession:
        session.updated_at = utc_now()
        self.db.flush()
        return session

    def create_message(
        self,
        workspace_id: str,
        role: MessageRole,
        content: str,
        user_id: str | None = None,
        session_id: str | None = None,
        attached_document_ids: list[str] | None = None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            workspace_id=workspace_id,
            session_id=session_id,
            user_id=user_id,
            role=role.value,
            content=content,
            attached_document_ids=attached_document_ids or [],
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

    def list_messages_for_session(
        self,
        workspace_id: str,
        session_id: str,
    ) -> list[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .where(
                ConversationMessage.workspace_id == workspace_id,
                ConversationMessage.session_id == session_id,
            )
            .order_by(ConversationMessage.created_at.asc())
        )

        return list(self.db.scalars(statement).all())


def _clean_title(title: str) -> str:
    cleaned = " ".join(title.strip().split())
    return cleaned[:180] or "New chat"
