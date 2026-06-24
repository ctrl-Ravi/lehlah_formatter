"""
Formatter handler – processes Lehlah collection text and produces deal output.

Features:
  - Inline action buttons (Copy Output / Process Another / Reset Template).
  - Bulk mode: multiple collections separated by `===`.
  - /markdown and /plain export commands.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.parser import (
    parse_template,
    parse_collection,
    split_bulk_collections,
)
from services.formatter import build_deal, FormattedDeal, format_plain
from services.database import get_template
from handlers.template import (
    STATE_KEY,
    STATE_IDLE,
    STATE_AWAITING,
    TEMPLATE_KEY,
    handle_template_save,
)

logger = logging.getLogger(__name__)

# Context key for last formatted output
LAST_OUTPUT_KEY = "last_output"


def _build_action_keyboard() -> InlineKeyboardMarkup:
    """Build the post-format inline keyboard."""
    buttons = [
        [
            InlineKeyboardButton("📋 Copy Output",      callback_data="copy_output"),
            InlineKeyboardButton("🔄 Process Another",  callback_data="process_another"),
        ],
        [
            InlineKeyboardButton("🗑 Reset Template", callback_data="reset_template"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main message dispatcher.

    State machine:
      IDLE          → treat incoming text as a new template.
      AWAITING_COLLECTION → treat incoming text as Lehlah collection data.
    """
    assert update.message is not None
    text    = (update.message.text or update.message.caption or "").strip()
    user_id = update.effective_user.id

    if not text:
        return

    # ── Auto-Detect Template vs Collection ──────────────────────────────────
    # If the text does not contain 'lehlah', assume it's a new template.
    # This allows users to switch templates automatically without pressing Reset.
    is_collection = "lehlah" in text.lower()

    if not is_collection:
        # Treat as a new template, automatically overriding the old one.
        await handle_template_save(update, context, text)
        return

    # It's a collection. Ensure we have a template to apply.
    state = context.user_data.get(STATE_KEY, STATE_IDLE)
    
    if state == STATE_IDLE:
        db_template = await get_template(user_id)
        if db_template:
            context.user_data[TEMPLATE_KEY] = db_template
            context.user_data[STATE_KEY]    = STATE_AWAITING
            await _process_collection(update, context, text)
        else:
            await update.message.reply_text(
                "⚠️ *No template found.*\n\n"
                "Please send your deal template first before sending a collection.",
                parse_mode="Markdown"
            )
    elif state == STATE_AWAITING:
        await _process_collection(update, context, text)
    else:
        context.user_data[STATE_KEY] = STATE_IDLE
        await update.message.reply_text(
            "⚠️ Something went wrong. State reset.\n\nPlease send your template again."
        )


async def _process_collection(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """
    Process one or more Lehlah collection blocks.

    Args:
        update:  Telegram Update.
        context: PTB context (must have TEMPLATE_KEY set in user_data).
        text:    Raw collection text (may contain multiple blocks via `===`).
    """
    assert update.message is not None
    user_id         = update.effective_user.id
    template_text   = context.user_data.get(TEMPLATE_KEY)

    if not template_text:
        await update.message.reply_text(
            "⚠️ No template found. Please send your deal template first."
        )
        context.user_data[STATE_KEY] = STATE_IDLE
        return

    parsed_template = parse_template(template_text)
    collection_blocks = split_bulk_collections(text)

    results: list[str] = []

    for idx, block in enumerate(collection_blocks, start=1):
        prefix = f"*Block {idx}:*\n" if len(collection_blocks) > 1 else ""

        # ── Platform detection (fully automatic – never ask the user) ──────
        parsed_collection = parse_collection(block)
        if parsed_collection is None:
            results.append(
                f"{prefix}"
                "❌ *Platform not detected.*\n\n"
                "Supported platforms:\n"
                "• Myntra\n"
                "• Flipkart\n"
                "• Ajio\n"
                "• Amazon\n\n"
                "Please verify the collection text."
            )
            continue

        result = build_deal(parsed_template, parsed_collection)

        if isinstance(result, str):
            # Mismatch / validation error from formatter
            results.append(f"{prefix}{result}")
        else:
            results.append(f"{prefix}{result.text}")

    combined_output = "\n\n---\n\n".join(results)

    # Store last output for /markdown and /plain commands
    context.user_data[LAST_OUTPUT_KEY] = combined_output

    # Advance state back to IDLE so next message is treated as a new template,
    # unless user wants to process another collection (handled via callback).
    context.user_data[STATE_KEY] = STATE_IDLE

    await update.message.reply_text(
        combined_output,
        reply_markup=_build_action_keyboard(),
        disable_web_page_preview=True,
    )
    logger.info(
        "User %d processed %d collection block(s)", user_id, len(collection_blocks)
    )


# ---------------------------------------------------------------------------
# Inline keyboard callbacks
# ---------------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    data = query.data

    if data == "copy_output":
        last = context.user_data.get(LAST_OUTPUT_KEY, "")
        if last:
            await query.message.reply_text(
                f"📋 *Here's your output to copy:*\n\n{last}",
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        else:
            await query.message.reply_text("⚠️ No output available yet.")

    elif data == "process_another":
        context.user_data[STATE_KEY] = STATE_AWAITING
        await query.message.reply_text(
            "🔄 Send the next *Lehlah Collection* text.",
            parse_mode="Markdown",
        )

    elif data == "reset_template":
        from services.database import delete_template
        user_id = update.effective_user.id
        await delete_template(user_id)
        context.user_data.clear()
        await query.message.reply_text(
            "🗑 Template reset. Send a new template whenever you're ready!"
        )


# ---------------------------------------------------------------------------
# Export commands
# ---------------------------------------------------------------------------

async def markdown_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """/markdown – Resend last output with Markdown formatting note."""
    assert update.message is not None
    last = context.user_data.get(LAST_OUTPUT_KEY)
    if not last:
        await update.message.reply_text(
            "⚠️ No output available. Process a collection first."
        )
        return

    await update.message.reply_text(
        f"📝 *Markdown Output:*\n\n`{last}`",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def plain_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/plain – Resend last output as plain text."""
    assert update.message is not None
    last = context.user_data.get(LAST_OUTPUT_KEY)
    if not last:
        await update.message.reply_text(
            "⚠️ No output available. Process a collection first."
        )
        return

    await update.message.reply_text(
        f"Plain Output:\n\n{format_plain(FormattedDeal(text=last, labels=[], links=[]))}",
        disable_web_page_preview=True,
    )
