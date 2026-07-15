import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.domain.chat_models import ChatMessageRecord, ChatRole


class ChatHistoryService:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._ensure_database()

    def append_message(
        self,
        *,
        session_id: str,
        actor_id: str,
        seat_position: str,
        role: ChatRole,
        text: str,
        user_id: str | None = None,
        trace_id: str | None = None,
        created_at: str | None = None,
    ) -> ChatMessageRecord:
        message = ChatMessageRecord(
            id=f"chat_{uuid4().hex[:16]}",
            session_id=session_id,
            actor_id=actor_id,
            user_id=user_id or actor_id,
            seat_position=seat_position,
            role=role,
            text=text,
            trace_id=trace_id,
            created_at=created_at or _utc_now_iso(),
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_messages (
                    id,
                    session_id,
                    actor_id,
                    user_id,
                    seat_position,
                    role,
                    text,
                    trace_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.session_id,
                    message.actor_id,
                    message.user_id,
                    message.seat_position,
                    message.role,
                    message.text,
                    message.trace_id,
                    message.created_at,
                ),
            )
        return message

    def list_messages(
        self,
        *,
        session_id: str,
        actor_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[ChatMessageRecord]:
        bounded_limit = max(1, min(limit, 500))
        params: list[object] = [session_id]
        actor_clause = ""
        user_clause = ""
        if actor_id is not None:
            actor_clause = "AND actor_id = ?"
            params.append(actor_id)
        if user_id is not None:
            user_clause = "AND user_id = ?"
            params.append(user_id)
        params.append(bounded_limit)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM (
                    SELECT
                        id, session_id, actor_id, user_id, seat_position,
                        role, text, trace_id, created_at
                    FROM chat_messages
                    WHERE session_id = ?
                    {actor_clause}
                    {user_clause}
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                )
                ORDER BY created_at ASC, id ASC
                """,
                params,
            ).fetchall()

        return [ChatMessageRecord.model_validate(dict(row)) for row in rows]

    def _ensure_database(self) -> None:
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    seat_position TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    text TEXT NOT NULL,
                    trace_id TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(chat_messages)").fetchall()
            }
            if "user_id" not in columns:
                connection.execute(
                    """
                    ALTER TABLE chat_messages
                    ADD COLUMN user_id TEXT NOT NULL DEFAULT ''
                    """
                )
                connection.execute(
                    """
                    UPDATE chat_messages
                    SET user_id = actor_id
                    WHERE user_id = ''
                    """
                )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_actor_created
                ON chat_messages (session_id, actor_id, created_at)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_actor_user_created
                ON chat_messages (session_id, actor_id, user_id, created_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
