# Deal Formatter Bot 🤖

A production-ready Telegram bot that converts **Lehlah collection links** into perfectly formatted affiliate deal posts.

---

## Features

| Feature | Details |
|---|---|
| Template storage | Per-user SQLite persistence |
| Smart formatting | Label ↔ link pairing with reversal logic |
| Platform detection | Myntra, Flipkart, Ajio, Amazon (configurable) |
| Bulk mode | Multiple collections via `===` separator |
| Mismatch validation | Clear error messages with counts |
| Inline buttons | Copy / Process Another / Reset after each output |
| Export modes | `/markdown` and `/plain` commands |
| Admin stats | `/stats` restricted by `ADMIN_IDS` env var |
| Async & typed | Full `async/await`, type hints, PEP 8 |

---

## Project Structure

```
deal_formatter_bot/
│
├── bot.py                  ← Entry point, handler wiring
│
├── handlers/
│   ├── start.py            ← /start, /help
│   ├── template.py         ← /show, /reset, template saving
│   ├── formatter.py        ← Collection processing, inline buttons, /markdown, /plain
│   └── admin.py            ← /stats (admin only)
│
├── services/
│   ├── parser.py           ← Template & collection parsing, platform detection
│   ├── formatter.py        ← Deal assembly & validation
│   └── database.py         ← Async SQLite via aiosqlite
│
└── data/
    └── bot.db              ← Auto-created at runtime
```

---

## Quick Start (Local)

### 1. Clone & set up environment

```bash
git clone <your-repo>
cd deal_formatter_bot

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321   # optional
```

### 3. Run

```bash
python deal_formatter_bot/bot.py
```

---

## User Flow

### Step 1 – Send Template

Send a deal template with labels and any placeholder URLs:

```
Myntra : Upto 90% Off On Highlander Men Clothing.

Shirts from 124 : https://myntr.it/abc
Tshirts from 119 : https://myntr.it/def
Trousers from 264 : https://myntr.it/ghi
```

Bot replies: `✅ Template saved. Now send Lehlah Collection text.`

### Step 2 – Send Lehlah Collection

Paste the Lehlah collection text:

```
Collection: Highlander

Collection URL:
https://app.lehlah.club/pc/211510

Product Links:

Myntra - Clothing
https://app.lehlah.club/share/abc123

Myntra - Clothing
https://app.lehlah.club/share/def456

Myntra - Highlander Shirts
https://app.lehlah.club/share/ghi789
```

Bot outputs:

```
Myntra : Upto 90% Off On Highlander Men Clothing.

Shirts from 124 : https://myntr.store/share/ghi789
Tshirts from 119 : https://myntr.store/share/def456
Trousers from 264 : https://myntr.store/share/abc123
```

---

## Commands Reference

| Command | Description | Who |
|---|---|---|
| `/start` | Welcome message | All |
| `/help` | Usage instructions | All |
| `/show` | Display saved template | All |
| `/reset` | Delete saved template | All |
| `/markdown` | Resend last output (Markdown) | All |
| `/plain` | Resend last output (plain text) | All |
| `/stats` | Bot statistics | Admin only |

---

## Bulk Mode

Separate multiple Lehlah collections with `===` in a single message:

```
Collection: Brand A
...links...
===
Collection: Brand B
...links...
```

The bot processes each block separately and outputs all results.

---

## Platform Mapping

Configured in `services/parser.py`:

```python
PLATFORM_DOMAIN_MAP = {
    "myntra":   "myntr.store",
    "flipkart": "fkrt.store",
    "ajio":     "ajiio.store",
    "amazon":   "amzn.store",
}
```

Add new platforms by extending this dictionary.

---

## Deployment

### Docker (Recommended)

```bash
# Build
docker build -t deal-formatter-bot .

# Run
docker run -d \
  --name deal-bot \
  --restart unless-stopped \
  -e BOT_TOKEN=your_token \
  -e ADMIN_IDS=123456789 \
  -v deal_bot_data:/app/deal_formatter_bot/data \
  deal-formatter-bot
```

---

### Render.com

1. Push your code to GitHub.
2. Create a new **Background Worker** service on Render.
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `python deal_formatter_bot/bot.py`
5. Add environment variables:
   - `BOT_TOKEN` = your token
   - `ADMIN_IDS` = your Telegram ID (optional)
6. Set **Instance Type** to at least "Starter" (free tier sleeps).
7. Deploy!

> **Tip:** Use a Render **Disk** (mount at `/app/deal_formatter_bot/data`) so the SQLite DB persists across deploys.

---

### Railway.app

1. Push your code to GitHub.
2. Create a new Railway project → **Deploy from GitHub repo**.
3. Railway auto-detects Python. Set the start command:
   ```
   python deal_formatter_bot/bot.py
   ```
4. Go to **Variables** and add:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
5. To persist the database, add a **Volume** mounted at `/app/deal_formatter_bot/data`.
6. Deploy!

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ Yes | Telegram Bot API token from @BotFather |
| `ADMIN_IDS` | No | Comma-separated Telegram IDs with admin access |

---

## Tech Stack

- **Python 3.12**
- **python-telegram-bot v22+** (async, ApplicationBuilder pattern)
- **aiosqlite** – async SQLite driver
- **python-dotenv** – environment variable loading

---

## License

MIT
