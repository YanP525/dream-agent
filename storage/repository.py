from datetime import datetime, timezone
import json

from storage.database import get_connection
from storage.models import DreamSession, Message, Profile

EMPTY_PSYCHE_MAP = {
    "symbols": [],
    "shadow": {"current_theme": "", "movement": "不明", "note": ""},
    "animus_anima": {"polarity": "未显", "movement": "不明", "note": ""},
    "complexes": [],
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _row_to_profile(row) -> Profile:
    return Profile(
        id=row["id"],
        display_name=row["display_name"],
        life_summary=row["life_summary"],
        stressors=row["stressors"],
        preferences=row["preferences"],
        psyche_map=row["psyche_map"] if "psyche_map" in row.keys() else "{}",
        updated_at=row["updated_at"],
    )


def _row_to_dream(row) -> DreamSession:
    return DreamSession(
        id=row["id"],
        title=row["title"],
        raw_dream=row["raw_dream"],
        status=row["status"],
        analyst_notes=row["analyst_notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_message(row) -> Message:
    return Message(
        id=row["id"],
        dream_id=row["dream_id"],
        role=row["role"],
        content=row["content"],
        created_at=row["created_at"],
    )


def get_profile() -> Profile | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return _row_to_profile(row) if row else None


def upsert_profile(
    display_name: str = "",
    life_summary: str = "",
    stressors: str = "",
    preferences: str = "",
) -> Profile:
    now = _now()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
        if existing:
            conn.execute(
                """
                UPDATE profile
                SET display_name = ?, life_summary = ?, stressors = ?,
                    preferences = ?, updated_at = ?
                WHERE id = 1
                """,
                (display_name, life_summary, stressors, preferences, now),
            )
        else:
            conn.execute(
                """
                INSERT INTO profile (id, display_name, life_summary, stressors, preferences, updated_at)
                VALUES (1, ?, ?, ?, ?, ?)
                """,
                (display_name, life_summary, stressors, preferences, now),
            )
        row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return _row_to_profile(row)


def get_psyche_map() -> dict:
    profile = get_profile()
    if not profile or not profile.psyche_map.strip():
        return dict(EMPTY_PSYCHE_MAP)
    try:
        data = json.loads(profile.psyche_map)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return dict(EMPTY_PSYCHE_MAP)


def update_psyche_map(data: dict) -> None:
    now = _now()
    payload = json.dumps(data, ensure_ascii=False)
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
        if existing:
            conn.execute(
                "UPDATE profile SET psyche_map = ?, updated_at = ? WHERE id = 1",
                (payload, now),
            )
        else:
            conn.execute(
                """
                INSERT INTO profile (id, display_name, life_summary, stressors, preferences, psyche_map, updated_at)
                VALUES (1, '', '', '', '', ?, ?)
                """,
                (payload, now),
            )


def profile_is_complete(profile: Profile | None) -> bool:
    if not profile:
        return False
    return bool(profile.life_summary.strip() and profile.stressors.strip())


def create_dream(raw_dream: str, title: str = "") -> DreamSession:
    now = _now()
    if not title:
        title = _auto_title(raw_dream)
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO dream_sessions (title, raw_dream, status, created_at, updated_at)
            VALUES (?, ?, 'exploring', ?, ?)
            """,
            (title, raw_dream, now, now),
        )
        dream_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM dream_sessions WHERE id = ?", (dream_id,)
        ).fetchone()
    return _row_to_dream(row)


def _auto_title(raw_dream: str, max_len: int = 24) -> str:
    text = raw_dream.strip().replace("\n", " ")
    if not text:
        return "未命名梦境"
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def get_dream(dream_id: int) -> DreamSession | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM dream_sessions WHERE id = ?", (dream_id,)
        ).fetchone()
    return _row_to_dream(row) if row else None


def list_dreams(limit: int = 50) -> list[DreamSession]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM dream_sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_to_dream(row) for row in rows]


def get_recent_dreams(limit: int = 5, exclude_id: int | None = None) -> list[DreamSession]:
    with get_connection() as conn:
        if exclude_id is not None:
            rows = conn.execute(
                """
                SELECT * FROM dream_sessions
                WHERE id != ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (exclude_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM dream_sessions
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [_row_to_dream(row) for row in rows]


def add_message(dream_id: int, role: str, content: str) -> Message:
    now = _now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO messages (dream_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (dream_id, role, content, now),
        )
        conn.execute(
            "UPDATE dream_sessions SET updated_at = ? WHERE id = ?",
            (now, dream_id),
        )
        row = conn.execute(
            "SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return _row_to_message(row)


def get_messages(dream_id: int) -> list[Message]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM messages
            WHERE dream_id = ?
            ORDER BY id ASC
            """,
            (dream_id,),
        ).fetchall()
    return [_row_to_message(row) for row in rows]


def update_dream_notes(dream_id: int, analyst_notes: str, status: str = "analyzed") -> None:
    now = _now()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE dream_sessions
            SET analyst_notes = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (analyst_notes, status, now, dream_id),
        )


def delete_dream(dream_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE dream_id = ?", (dream_id,))
        conn.execute("DELETE FROM dream_sessions WHERE id = ?", (dream_id,))
