"""
Formatter service for Deal Formatter Bot.

Merges a ParsedTemplate with a ParsedCollection to produce the final
formatted deal text, handling mismatch validation.
"""

import logging
from .parser import ParsedTemplate, ParsedCollection, FormattedDeal

logger = logging.getLogger(__name__)


def build_deal(
    parsed_template: ParsedTemplate,
    parsed_collection: ParsedCollection,
) -> FormattedDeal | str:
    """
    Combine template labels with collection share-links to build a deal post.

    Args:
        parsed_template:   Labels and header extracted from the user's template.
        parsed_collection: Share-links extracted from the Lehlah collection.

    Returns:
        FormattedDeal on success, or an error string on mismatch.
    """
    old_urls = parsed_template.urls
    new_urls = parsed_collection.share_links

    # ── Validation ───────────────────────────────────────────────────────────
    if len(old_urls) != len(new_urls):
        error_msg = (
            "❌ *Mismatch detected*\n\n"
            f"Links in Template: *{len(old_urls)}*\n"
            f"Links in Collection: *{len(new_urls)}*\n\n"
            "Please check your input and try again."
        )
        logger.warning(
            "Mismatch – template_links=%d collection_links=%d", len(old_urls), len(new_urls)
        )
        return error_msg

    # ── Format ───────────────────────────────────────────────────────────────
    # Replace URLs exactly as they appear in the raw text
    text = parsed_template.raw_text
    for old_url, new_url in zip(old_urls, new_urls):
        text = text.replace(old_url, new_url, 1)

    # Automatically add the Upvote footer if the user didn't already put it in the template
    if "Upvote if this deal helped you" not in text:
        text += "\n\n⬆️ Upvote if this deal helped you."

    logger.debug("Deal formatted successfully (%d items)", len(new_urls))
    return FormattedDeal(text=text, labels=[], links=new_urls)


def format_markdown(deal: FormattedDeal) -> str:
    """Return deal text suitable for Telegram MarkdownV2 (escaped)."""
    # For /markdown command – wrap links as plain text (Telegram renders them)
    return deal.text


def format_plain(deal: FormattedDeal) -> str:
    """Return deal text as plain text (no markdown)."""
    return deal.text
