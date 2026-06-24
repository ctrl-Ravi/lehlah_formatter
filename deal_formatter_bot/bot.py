"""
Deal Formatter Bot – main entry point.

Wires up all handlers, initializes the database, and starts polling.
"""

import asyncio
import logging
import os
import sys
import time
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

# ── Path bootstrap ──────────────────────────────────────────────────────────
# Allow absolute imports from the deal_formatter_bot package root.
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Load environment ─────────────────────────────────────────────────────────
load_dotenv(ROOT.parent / ".env")

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Handler imports (after sys.path is set) ──────────────────────────────────
from handlers.start import start_command, help_command          # noqa: E402
from handlers.template import show_command, reset_command       # noqa: E402
from handlers.formatter import (                                # noqa: E402
    handle_message,
    handle_callback,
    markdown_command,
    plain_command,
)
from handlers.admin import stats_command                        # noqa: E402
from services.database import init_db                           # noqa: E402


# ── Bot commands menu ─────────────────────────────────────────────────────────
BOT_COMMANDS: list[BotCommand] = [
    BotCommand("start",    "Welcome message"),
    BotCommand("help",     "Usage instructions"),
    BotCommand("show",     "Show saved template"),
    BotCommand("reset",    "Delete saved template"),
    BotCommand("markdown", "Resend last output (Markdown mode)"),
    BotCommand("plain",    "Resend last output (plain-text mode)"),
    BotCommand("stats",    "Bot statistics (admin only)"),
]


async def post_init(application: Application) -> None:
    """Runs once after the application is built – sets the bot command menu."""
    await application.bot.set_my_commands(BOT_COMMANDS)
    logger.info("Bot command menu registered.")


def build_application(token: str) -> Application:
    """
    Build and configure the PTB Application instance.

    Args:
        token: Telegram Bot API token.

    Returns:
        Configured Application ready to run.
    """
    app = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .post_init(post_init)
        .build()
    )

    # ── Command handlers ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",    start_command))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("show",     show_command))
    app.add_handler(CommandHandler("reset",    reset_command))
    app.add_handler(CommandHandler("markdown", markdown_command))
    app.add_handler(CommandHandler("plain",    plain_command))
    app.add_handler(CommandHandler("stats",    stats_command))

    # ── Message handler (text and captions, no commands) ─────────────────────
    app.add_handler(
        MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, handle_message)
    )

    # ── Inline keyboard callback handler ──────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_callback))

    return app


# ── Keep-Alive / Health Check ───────────────────────────────────────────────
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
        
    def log_message(self, format, *args):
        pass # Suppress HTTP logs

def keep_alive():
    """Runs a dummy HTTP server for Render health checks and pings itself."""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info(f"KeepAlive: Dummy HTTP server running on port {port}")

    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        logger.info("KeepAlive: RENDER_EXTERNAL_URL not set, skipping self-ping")
        return

    logger.info(f"KeepAlive: pinging {url} every 5 minutes...")
    while True:
        try:
            urllib.request.urlopen(url, timeout=10)
            logger.info("KeepAlive: ping sent ✓")
        except Exception as e:
            logger.error(f"KeepAlive: something went wrong — {e}")
        time.sleep(300)

def main() -> None:
    """Main function – initialise DB then start the bot."""
    # Start the keep-alive background thread
    threading.Thread(target=keep_alive, daemon=True).start()

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.critical("BOT_TOKEN is not set. Please configure your .env file.")
        sys.exit(1)

    logger.info("Initializing database …")
    # init_db is async, so we run it using the current event loop context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    logger.info("Starting Deal Formatter Bot …")
    app = build_application(token)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
