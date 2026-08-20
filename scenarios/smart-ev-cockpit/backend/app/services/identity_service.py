import sqlite3
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from app.domain.identity_models import UserIdentity, UserProfileSummary
from app.powercontext.client import PowerContextClient
from app.powercontext.mappers import powercontext_hit_to_record

DEFAULT_IDENTITIES = (
    {
        "actor_id": "driver_primary",
        "seat_position": "front_left",
        "user_id": "driver_primary",
        "display_name": "Driver",
    },
    {
        "actor_id": "passenger_front",
        "seat_position": "front_right",
        "user_id": "passenger_front",
        "display_name": "Passenger",
    },
    {
        "actor_id": "child_rear_left",
        "seat_position": "rear_left",
        "user_id": "child_rear_left",
        "display_name": "Child",
    },
)


class UnknownIdentityError(KeyError):
    pass


class IdentityService:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._ensure_database()

    def list_identities(self) -> list[UserIdentity]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT actor_id, seat_position, user_id, display_name, profile_note, updated_at
                FROM user_identities
                ORDER BY sort_order ASC
                """
            ).fetchall()
        return [UserIdentity.model_validate(dict(row)) for row in rows]

    def get_identity(self, actor_id: str) -> UserIdentity:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT actor_id, seat_position, user_id, display_name, profile_note, updated_at
                FROM user_identities
                WHERE actor_id = ?
                """,
                (actor_id,),
            ).fetchone()
        if row is None:
            raise UnknownIdentityError(actor_id)
        return UserIdentity.model_validate(dict(row))

    def update_identity(
        self,
        actor_id: str,
        *,
        user_id: str,
        display_name: str | None = None,
        profile_note: str | None = None,
    ) -> UserIdentity:
        current = self.get_identity(actor_id)
        next_display_name = display_name if display_name is not None else current.display_name
        next_profile_note = profile_note if profile_note is not None else current.profile_note
        updated_at = _utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE user_identities
                SET user_id = ?, display_name = ?, profile_note = ?, updated_at = ?
                WHERE actor_id = ?
                """,
                (
                    user_id.strip(),
                    next_display_name.strip(),
                    next_profile_note.strip(),
                    updated_at,
                    actor_id,
                ),
            )
        return self.get_identity(actor_id)

    def get_profile(
        self,
        actor_id: str,
        *,
        powercontext_client: PowerContextClient,
        limit: int = 24,
    ) -> UserProfileSummary:
        identity = self.get_identity(actor_id)
        rows = powercontext_client.list_memories(
            filters={
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
            },
            user_id=identity.user_id,
            limit=limit,
        )
        memories = [powercontext_hit_to_record(row) for row in rows]
        memories.sort(
            key=lambda memory: (
                memory.metadata.memory_kind != "person_profile",
                memory.memory_id,
            )
        )
        counts = Counter(memory.metadata.memory_kind for memory in memories)
        primary = next(
            (
                memory.content
                for memory in memories
                if memory.metadata.memory_kind == "person_profile"
            ),
            memories[0].content if memories else None,
        )
        return UserProfileSummary(
            identity=identity,
            primary_memory=primary,
            memory_kind_counts=dict(sorted(counts.items())),
            memories=memories,
        )

    def _ensure_database(self) -> None:
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_identities (
                    actor_id TEXT PRIMARY KEY,
                    seat_position TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    profile_note TEXT NOT NULL DEFAULT '',
                    sort_order INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            now = _utc_now_iso()
            for index, identity in enumerate(DEFAULT_IDENTITIES):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO user_identities (
                        actor_id,
                        seat_position,
                        user_id,
                        display_name,
                        profile_note,
                        sort_order,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, '', ?, ?)
                    """,
                    (
                        identity["actor_id"],
                        identity["seat_position"],
                        identity["user_id"],
                        identity["display_name"],
                        index,
                        now,
                    ),
                )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
