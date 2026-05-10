"""
Valura AI — Session Memory Manager.

SQLite-backed persistent session memory with async I/O.
Stores conversation history, agent outputs, and user preferences.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from src.core.config import get_settings
from src.core.logging import get_logger
from src.models.schemas import SessionMessage, RiskProfile

logger = get_logger("memory")

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    risk_profile TEXT DEFAULT 'moderate',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    agents_used TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    session_id TEXT PRIMARY KEY,
    risk_profile TEXT DEFAULT 'moderate',
    watched_tickers TEXT DEFAULT '[]',
    portfolio TEXT DEFAULT '[]',
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
"""


class SessionManager:
    """
    Async SQLite-backed session memory.

    Provides:
    - Session CRUD
    - Message history storage/retrieval
    - User preference persistence
    - Windowed context for LLM
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or get_settings().db_path
        self._initialized = False

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        if self._initialized:
            return
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(CREATE_TABLES_SQL)
            await db.commit()
        self._initialized = True
        logger.info(f"Session DB initialized at {self._db_path}")

    async def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session, return session_id."""
        await self.initialize()
        sid = session_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at) VALUES (?, ?, ?)",
                (sid, now, now),
            )
            await db.commit()
        return sid

    async def add_message(
        self, session_id: str, role: str, content: str,
        agents_used: list[str] | None = None, metadata: dict | None = None,
    ) -> None:
        """Add a message to session history."""
        await self.initialize()
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._db_path) as db:
            # Ensure session exists
            await db.execute(
                "INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at) VALUES (?, ?, ?)",
                (session_id, now, now),
            )
            await db.execute(
                "INSERT INTO messages (session_id, role, content, agents_used, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, role, content, json.dumps(agents_used or []),
                 json.dumps(metadata or {}), now),
            )
            await db.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            await db.commit()

    async def get_messages(
        self, session_id: str, limit: Optional[int] = None,
    ) -> list[SessionMessage]:
        """Get message history for a session."""
        await self.initialize()
        limit = limit or get_settings().memory_window
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT role, content, agents_used, metadata, created_at FROM messages "
                "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            )
            rows = await cursor.fetchall()

        messages = []
        for row in reversed(rows):  # Reverse to chronological order
            messages.append(SessionMessage(
                role=row["role"],
                content=row["content"],
                agents_used=json.loads(row["agents_used"]),
                metadata=json.loads(row["metadata"]),
                timestamp=datetime.fromisoformat(row["created_at"]),
            ))
        return messages

    async def get_risk_profile(self, session_id: str) -> RiskProfile:
        """Get user's risk profile for a session."""
        await self.initialize()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT risk_profile FROM sessions WHERE session_id = ?", (session_id,),
            )
            row = await cursor.fetchone()
            if row and row[0]:
                try:
                    return RiskProfile(row[0])
                except ValueError:
                    pass
        return RiskProfile.MODERATE

    async def set_risk_profile(self, session_id: str, profile: RiskProfile) -> None:
        """Set user's risk profile."""
        await self.initialize()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE sessions SET risk_profile = ? WHERE session_id = ?",
                (profile.value, session_id),
            )
            await db.commit()

    async def get_session_count(self) -> int:
        """Get total number of active sessions."""
        await self.initialize()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM sessions")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages."""
        await self.initialize()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            await db.execute("DELETE FROM user_preferences WHERE session_id = ?", (session_id,))
            await db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            await db.commit()
