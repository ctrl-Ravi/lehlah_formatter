# ── Stage 1: build deps ───────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into a virtual environment for clean layering
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN addgroup --system bot && adduser --system --ingroup bot bot

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY deal_formatter_bot/ ./deal_formatter_bot/

# Ensure the data directory exists and is writable by the bot user
RUN mkdir -p /app/deal_formatter_bot/data \
 && chown -R bot:bot /app

USER bot

# Health: python is importable
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import telegram" || exit 1

CMD ["python", "deal_formatter_bot/bot.py"]
