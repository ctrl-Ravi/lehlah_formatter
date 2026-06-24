"""
Parser service for Deal Formatter Bot.

Responsibilities:
  - Extract the header, labels and URLs from a deal template.
  - Extract Lehlah collection share-links from collection text.
  - Detect the target platform (Myntra, Flipkart, Ajio, Amazon).
  - Replace the Lehlah CDN domain with the platform-specific short domain.
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform mapping  (configurable – add new platforms here)
# ---------------------------------------------------------------------------
PLATFORM_DOMAINS: dict[str, str] = {
    "myntra":   "myntr.store",
    "flipkart": "fkrt.store",
    "ajio":     "ajiio.store",
    "amazon":   "amzn.store",
}

LEHLAH_BASE_URL = "https://app.lehlah.club"

# Regex patterns
_URL_PATTERN      = re.compile(r"https?://\S+")
_LEHLAH_SHARE     = re.compile(r"https?://app\.lehlah\.club/share/\S+")
_COLLECTION_HEADER = re.compile(r"^Collection(?:\s*URL)?\s*:", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ParsedTemplate:
    """Represents a parsed deal template."""
    header: str
    labels: list[str]


@dataclass
class ParsedCollection:
    """Represents a parsed Lehlah collection block."""
    platform: str
    share_links: list[str]


@dataclass
class FormattedDeal:
    """Final formatted deal ready to send."""
    text: str
    labels: list[str]
    links: list[str]


# ---------------------------------------------------------------------------
# Template parsing
# ---------------------------------------------------------------------------

def parse_template(template: str) -> ParsedTemplate:
    """
    Extract the header text and ordered list of labels from a deal template.

    The template is expected to look like:
        Myntra : Upto 90% Off …

        Shirts from 124 : https://myntr.it/xxx
        Tshirts from 119 : https://myntr.it/yyy
        …

    Args:
        template: Raw template text as sent by the user.

    Returns:
        ParsedTemplate with `header` and `labels`.
    """
    lines = template.strip().splitlines()

    header_lines: list[str] = []
    labels: list[str] = []
    buffer: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if _URL_PATTERN.search(stripped):
            # Extract the label part from this line (if any)
            inline_label = _URL_PATTERN.sub("", stripped).rstrip(" :|-").strip()
            
            if inline_label:
                # Label and URL are on the same line
                if not labels:
                    header_lines.extend(buffer)
                buffer = []
                labels.append(inline_label)
            else:
                # URL is on its own line; use the last buffered line as its label
                if buffer:
                    label = buffer.pop()
                    if not labels:
                        header_lines.extend(buffer)
                    labels.append(label.rstrip(" :|-").strip())
                    buffer = []
                else:
                    labels.append("Item")
        else:
            buffer.append(stripped)

    # Any remaining unassigned lines belong to the header if no labels were found yet
    if not labels:
        header_lines.extend(buffer)

    header = "\n".join(header_lines).strip()
    logger.debug("Parsed template – header: %r, labels: %s", header, labels)
    return ParsedTemplate(header=header, labels=labels)


# ---------------------------------------------------------------------------
# Collection parsing
# ---------------------------------------------------------------------------

def detect_domain(collection_text: str) -> str | None:
    """
    Automatically detect the target short domain from collection text.

    Searches the full collection text (case-insensitive) for a known platform
    name and returns the corresponding replacement domain.

    Args:
        collection_text: Raw collection text from Lehlah.

    Returns:
        Domain string (e.g. ``"myntr.store"``), or ``None`` if no supported
        platform is found. Never returns an empty string.
    """
    text = collection_text.lower()
    for platform, domain in PLATFORM_DOMAINS.items():
        if platform in text:
            logger.debug("Detected platform '%s' -> domain '%s'", platform, domain)
            return domain
    logger.warning("No platform detected in collection text.")
    return None


def extract_share_links(collection_text: str) -> list[str]:
    """
    Extract all Lehlah share links from the collection text.

    Args:
        collection_text: Raw collection text from Lehlah.

    Returns:
        List of raw share link strings.
    """
    links = _LEHLAH_SHARE.findall(collection_text)
    logger.debug("Extracted %d share links", len(links))
    return links


def parse_collection(collection_text: str) -> ParsedCollection | None:
    """
    Parse a Lehlah collection block.

    Processing order (fully automatic – no user interaction required):
      1. Detect platform from collection text.
      2. Extract all Lehlah share links.
      3. Reverse link order (Lehlah order is always the opposite of template order).
      4. Convert every link's base URL to the platform-specific short domain.

    Args:
        collection_text: Raw collection text sent by the user.

    Returns:
        ParsedCollection on success, or ``None`` if the platform cannot be
        detected (caller must send the user an appropriate error message).
    """
    domain = detect_domain(collection_text)
    if domain is None:
        return None

    raw_links = extract_share_links(collection_text)

    # Lehlah lists newest → oldest; template is oldest → newest, so reverse.
    raw_links.reverse()

    # Replace full base URL so the https:// scheme is preserved correctly.
    replaced_links = [
        link.replace(LEHLAH_BASE_URL, f"https://{domain}")
        for link in raw_links
    ]

    return ParsedCollection(platform=domain, share_links=replaced_links)


# ---------------------------------------------------------------------------
# Bulk collection splitting
# ---------------------------------------------------------------------------

BULK_SEPARATOR = "==="


def split_bulk_collections(text: str) -> list[str]:
    """
    Split a bulk message into individual collection blocks.

    Args:
        text: Full message text possibly containing multiple collections
              separated by `===`.

    Returns:
        List of individual collection block strings.
    """
    parts = [p.strip() for p in text.split(BULK_SEPARATOR) if p.strip()]
    return parts
