"""
Template management handlers.

Handles:
  - /show  : display saved template
  - /reset : delete saved template
  - Saving a new template when user is in the IDLE conversation state
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from services.database import save_template, get_template, delete_template

logger = logging.getLogger(__name__)

# Conversation state keys stored in context.user_data
STATE_KEY       = "state"
STATE_IDLE      = "IDLE"
STATE_AWAITING  = "AWAITING_COLLECTION"
TEMPLATE_KEY    = "template"


async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/show – Display the user's currently saved template."""
    assert update.message is not None
    user_id  = update.effective_user.id
    template = await get_template(user_id)

    if template:
        await update.message.reply_text(
            f"📋 *Your saved template:*\n\n{template}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "⚠️ You don't have a saved template yet.\n\n"
            "Send me a deal template to get started!"
        )
    logger.info("User %d viewed their template", user_id)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reset – Delete the user's saved template and reset state."""
    assert update.message is not None
    user_id = update.effective_user.id

    deleted = await delete_template(user_id)

    # Also clear in-memory state
    context.user_data.clear()

    if deleted:
        await update.message.reply_text(
            "🗑 Template deleted successfully.\n\n"
            "Send a new template whenever you're ready!"
        )
    else:
        await update.message.reply_text(
            "ℹ️ No template found to delete."
        )
    logger.info("User %d reset their template (deleted=%s)", user_id, deleted)


async def handle_template_save(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """
    Save the received text as the user's deal template.

    Called from the main message dispatcher when the user is in IDLE state.

    Args:
        update:  Telegram Update object.
        context: PTB context.
        text:    Message text to save as template.
    """
    assert update.message is not None
    user_id = update.effective_user.id

    await save_template(user_id, text)

    # Store template in session and advance state
    context.user_data[TEMPLATE_KEY] = text
    context.user_data[STATE_KEY]    = STATE_AWAITING

    await update.message.reply_text(
        "✅ *Template saved.*\n\n"
        "Now send the *Lehlah Collection* text.",
        parse_mode="Markdown",
    )
    logger.info("User %d saved a new template", user_id)
