"""
Admin command handlers.

All commands in this module are restricted to ADMIN_IDS loaded from .env.
"""

import logging
import os
from functools import wraps
from typing import Callable, Awaitable

from telegram import Update
from telegram.ext import ContextTypes

from services.database import get_stats

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Admin ID loading
# ---------------------------------------------------------------------------

def _load_admin_ids() -> set[int]:
    """Load admin IDs from ADMIN_IDS environment variable."""
    raw = os.getenv("ADMIN_IDS", "")
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    logger.info("Loaded %d admin ID(s)", len(ids))
    return ids


ADMIN_IDS: set[int] = _load_admin_ids()


# ---------------------------------------------------------------------------
# Admin guard decorator
# ---------------------------------------------------------------------------

def admin_only(
    func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]:
    """Decorator that restricts a handler to admin users only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            assert update.message is not None
            await update.message.reply_text("🚫 You are not authorized to use this command.")
            logger.warning("Unauthorized /stats attempt by user %d", user_id)
            return
        await func(update, context)
    return wrapper


# ---------------------------------------------------------------------------
# Admin commands
# ---------------------------------------------------------------------------

@admin_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/stats – Show bot usage statistics (admin only)."""
    assert update.message is not None

    data = await get_stats()

    text = (
        "📊 *Bot Statistics*\n\n"
        f"👥 Users:              *{data['total_users']}*\n"
        f"📋 Templates Stored:   *{data['templates_stored']}*\n"
    )

    await update.message.reply_text(text, parse_mode="Markdown")
    logger.info("Admin %d viewed /stats", update.effective_user.id)
