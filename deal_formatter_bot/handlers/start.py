"""
/start and /help command handlers.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 *Welcome to Deal Formatter Bot!*\n\n"
    "I help affiliate marketers convert Lehlah collection links "
    "into perfectly formatted deal posts.\n\n"
    "*How to use:*\n"
    "1️⃣ Send your deal *template* (with labels & old links).\n"
    "2️⃣ I'll save it and ask for your Lehlah collection text.\n"
    "3️⃣ Paste the collection — I'll generate a ready-to-post deal! 🚀\n\n"
    "Type /help for detailed instructions."
)

HELP_TEXT = (
    "📖 *Deal Formatter Bot – Instructions*\n\n"
    "*Step 1 – Send your template*\n"
    "Send a deal template with labels and existing URLs.\n"
    "_Example:_\n"
    "```\n"
    "Myntra : Upto 90% Off On Highlander Men Clothing.\n\n"
    "Shirts from 124 : https://myntr.it/abc\n"
    "Tshirts from 119 : https://myntr.it/def\n"
    "```\n\n"
    "*Step 2 – Send the Lehlah Collection text*\n"
    "Paste the collection text you copied from Lehlah.\n\n"
    "*Bulk Mode*\n"
    "Separate multiple collections with `===`\n\n"
    "*Commands:*\n"
    "/start – Welcome message\n"
    "/help  – This help page\n"
    "/show  – View your saved template\n"
    "/reset – Delete your saved template\n"
    "/markdown – Get last output in Markdown mode\n"
    "/plain    – Get last output in plain-text mode\n"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    assert update.message is not None
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
    logger.info("User %d triggered /start", update.effective_user.id)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    assert update.message is not None
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")
    logger.info("User %d triggered /help", update.effective_user.id)
