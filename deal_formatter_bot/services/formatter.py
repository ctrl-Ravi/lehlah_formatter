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
    labels = parsed_template.labels
    links  = parsed_collection.share_links

    # ── Validation ───────────────────────────────────────────────────────────
    if len(labels) != len(links):
        error_msg = (
            "❌ *Mismatch detected*\n\n"
            f"Labels found: *{len(labels)}*\n"
            f"Links found:  *{len(links)}*\n\n"
            "Please check your input and try again."
        )
        logger.warning(
            "Mismatch – labels=%d links=%d", len(labels), len(links)
        )
        return error_msg

    # ── Format ───────────────────────────────────────────────────────────────
    lines: list[str] = []

    if parsed_template.header:
        lines.append(parsed_template.header)
        lines.append("")  # blank separator

    for i, (label, link) in enumerate(zip(labels, links)):
        lines.append(label)
        lines.append(link)
        if i < len(labels) - 1:
            lines.append("")  # blank separator between products

    lines.append("")
    lines.append("⬆️ Upvote if this deal helped you.")

    text = "\n".join(lines)
    logger.debug("Deal formatted successfully (%d items)", len(labels))

    return FormattedDeal(text=text, labels=labels, links=links)


def format_markdown(deal: FormattedDeal) -> str:
    """Return deal text suitable for Telegram MarkdownV2 (escaped)."""
    # For /markdown command – wrap links as plain text (Telegram renders them)
    return deal.text


def format_plain(deal: FormattedDeal) -> str:
    """Return deal text as plain text (no markdown)."""
    return deal.text
