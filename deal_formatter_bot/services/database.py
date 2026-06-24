"""
Database service for Deal Formatter Bot.
Handles all SQLite operations using aiosqlite for async support.
"""

import logging
import aiosqlite
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the database file
DB_PATH = Path(__file__).parent.parent / "data" / "bot.db"


async def init_db() -> None:
    """Initialize database and create tables if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                template    TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


async def save_template(telegram_id: int, template: str) -> None:
    """
    Insert or update a user's deal template.

    Args:
        telegram_id: Telegram user ID.
        template:    Raw template text sent by the user.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (telegram_id, template, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                template   = excluded.template,
                created_at = excluded.created_at
            """,
            (telegram_id, template, datetime.utcnow()),
        )
        await db.commit()
    logger.debug("Template saved for user %d", telegram_id)


async def get_template(telegram_id: int) -> str | None:
    """
    Retrieve a user's saved template.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        Template string or None if not found.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT template FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
    return row[0] if row else None


async def delete_template(telegram_id: int) -> bool:
    """
    Delete a user's saved template.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        True if a record was deleted, False otherwise.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        await db.commit()
    deleted = cursor.rowcount > 0
    if deleted:
        logger.debug("Template deleted for user %d", telegram_id)
    return deleted


async def get_stats() -> dict:
    """
    Return aggregate statistics for admin use.

    Returns:
        Dict with total_users and templates_stored counts.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users: int = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE template IS NOT NULL"
        ) as cur:
            templates_stored: int = (await cur.fetchone())[0]

    return {"total_users": total_users, "templates_stored": templates_stored}
