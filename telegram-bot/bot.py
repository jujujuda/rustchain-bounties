"""
RustChain Telegram Bot — @RustChainBot
Checks wallet balance, miner status, and epoch info on RustChain.
"""

import os
import time
import logging
from functools import wraps
from typing import Optional

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── Config ──────────────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Primary RustChain node (RIP-200)
NODE_URL = os.getenv("NODE_URL", "https://50.28.86.131")
FALLBACK_NODE = os.getenv("FALLBACK_NODE", "https://50.28.86.132")
# Rate limit: 1 request per user per 5 seconds
RATE_LIMIT_SECONDS = 5
# Wallet for payment in bounty claims
RTC_WALLET = "RTC2fe3c33c77666ff76a1cd0999fd4466ee81250ff"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────

user_last_request: dict[int, float] = {}


def rate_limit(func):
    """Enforce 1 request per user per RATE_LIMIT_SECONDS."""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        now = time.time()
        last = user_last_request.get(user_id, 0)
        if now - last < RATE_LIMIT_SECONDS:
            remaining = round(RATE_LIMIT_SECONDS - (now - last), 1)
            await update.message.reply_text(
                f"⏳ Slow down! Try again in {remaining}s.\n"
                "Rate limit: 1 request per user every 5 seconds."
            )
            return
        user_last_request[user_id] = now
        return await func(update, context, *args, **kwargs)

    return wrapped


# ─── Node Helpers ─────────────────────────────────────────────────────────────

def get_node_url() -> str:
    """Return the primary node URL (fallback on failure)."""
    return NODE_URL


def check_node_health(url: str) -> bool:
    """Ping the RustChain node health endpoint."""
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def get_node() -> str:
    """Return the first responsive node URL."""
    for node in [NODE_URL, FALLBACK_NODE]:
        if check_node_health(node):
            return node
    return NODE_URL  # fall back anyway, error handling in caller


# ─── RustChain API Calls ──────────────────────────────────────────────────────

def fetch_balance(wallet: str) -> dict:
    """Fetch RTC balance for a wallet/miner_id."""
    node = get_node()
    try:
        resp = requests.get(
            f"{node}/wallet/balance",
            params={"miner_id": wallet},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"ok": True, "data": data, "node": node}
        elif resp.status_code == 404:
            return {"ok": False, "error": "Wallet not found", "node": node}
        else:
            return {"ok": False, "error": f"HTTP {resp.status_code}", "node": node}
    except Exception as e:
        return {"ok": False, "error": str(e), "node": node}


def fetch_miners() -> dict:
    """Fetch active miners list."""
    node = get_node()
    try:
        resp = requests.get(f"{node}/api/miners", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"ok": True, "data": data, "node": node}
        else:
            return {"ok": False, "error": f"HTTP {resp.status_code}", "node": node}
    except Exception as e:
        return {"ok": False, "error": str(e), "node": node}


def fetch_epoch() -> dict:
    """Fetch current epoch info."""
    node = get_node()
    try:
        resp = requests.get(f"{node}/epoch", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"ok": True, "data": data, "node": node}
        else:
            return {"ok": False, "error": f"HTTP {resp.status_code}", "node": node}
    except Exception as e:
        return {"ok": False, "error": str(e), "node": node}


# ─── Commands ─────────────────────────────────────────────────────────────────

@rate_limit
async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /balance <wallet> command."""
    if not context.args:
        await update.message.reply_text(
            "📖 Usage: /balance <wallet>\n"
            "Example: /balance RTC2fe3c33c77666ff76a1cd0999fd4466ee81250ff"
        )
        return

    wallet = context.args[0].strip()
    await update.message.reply_text(f"🔍 Checking balance for `{wallet}`...", parse_mode="Markdown")

    result = fetch_balance(wallet)

    if not result["ok"]:
        await update.message.reply_text(
            f"❌ Failed to fetch balance.\n"
            f"Node: {result['node']}\n"
            f"Error: {result['error']}\n\n"
            "The node may be offline. Try again shortly."
        )
        return

    data = result["data"]
    # Normalise response — field names vary by node version
    balance = data.get("balance") or data.get("rtc_balance") or data.get("amount") or 0
    status = data.get("status", "active")
    last_seen = data.get("last_seen") or data.get("last_active") or "unknown"

    await update.message.reply_text(
        f"✅ *Wallet Balance*\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👛 Wallet: `{wallet}`\n"
        f"💰 Balance: *{balance} RTC*\n"
        f"📊 Status: {status}\n"
        f"🕐 Last Active: {last_seen}\n"
        f"🔗 Node: {result['node']}",
        parse_mode="Markdown",
    )


@rate_limit
async def cmd_miners(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /miners command — list active miners."""
    await update.message.reply_text("⛏️ Fetching active miners...")

    result = fetch_miners()

    if not result["ok"]:
        await update.message.reply_text(
            f"❌ Failed to fetch miners.\n"
            f"Node: {result['node']}\n"
            f"Error: {result['error']}"
        )
        return

    data = result["data"]
    miners = data if isinstance(data, list) else data.get("miners", [])
    count = len(miners)

    if not miners:
        await update.message.reply_text(
            "ℹ️ No active miners found.\n"
            "The network may be starting up."
        )
        return

    # Show top 10 miners
    lines = ["⛏️ *Active Miners* (showing top 10)\n"]
    for m in miners[:10]:
        miner_id = m.get("miner_id") or m.get("id") or m.get("wallet", "?")
        arch = m.get("architecture") or m.get("arch", "?")
        power = m.get("hash_rate") or m.get("power", "?")
        lines.append(f"• `{miner_id[:20]}` — {arch} — {power}")
    lines.append(f"\n__{count} total miners on {result['node']}__")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@rate_limit
async def cmd_epoch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /epoch command — current epoch info."""
    await update.message.reply_text("📡 Fetching epoch info...")

    result = fetch_epoch()

    if not result["ok"]:
        await update.message.reply_text(
            f"❌ Failed to fetch epoch.\n"
            f"Node: {result['node']}\n"
            f"Error: {result['error']}"
        )
        return

    data = result["data"]
    epoch = data.get("epoch", "?")
    slot = data.get("slot", "?")
    height = data.get("height", "?")
    rewards = data.get("epoch_rewards") or data.get("rewards", "?")
    active_miners = data.get("active_miners") or data.get("miners", "?")

    await update.message.reply_text(
        f"📊 *Current Epoch*\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🔢 Epoch: *{epoch}*\n"
        f"⏱️  Slot: {slot}\n"
        f"🔗 Block Height: {height}\n"
        f"💰 Epoch Rewards: {rewards} RTC\n"
        f"⛏️  Active Miners: {active_miners}\n"
        f"🔗 Node: {result['node']}",
        parse_mode="Markdown",
    )


async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /price command — show RTC reference rate."""
    await update.message.reply_text(
        "💵 *RTC Reference Rate*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "🪙 1 RTC = *$0.10 USD* _(internal reference rate)_\n\n"
        "_Note: RTC is earned through mining and bounty participation, "
        "not traded on public exchanges._\n\n"
        "Earn RTC: https://github.com/Scottcjn/rustchain-bounties",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        "🤖 *RustChain Bot — Commands*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "*/balance <wallet>* — Check RTC balance\n"
        "*/miners* — List active miners\n"
        "*/epoch* — Current epoch info\n"
        "*/price* — RTC reference rate\n"
        "*/help* — Show this message\n"
        "━━━━━━━━━━━━━━━━━\n"
        "⏳ Rate limit: 1 request / 5 seconds per user\n"
        "🔗 Powered by RustChain (Proof-of-Antiquity)\n"
        "💰 Bounty: https://github.com/Scottcjn/rustchain-bounties/issues/2869",
        parse_mode="Markdown",
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — greet the user."""
    await update.message.reply_text(
        "👋 Welcome to the RustChain Bot!\n\n"
        "Check wallet balances, miner status, and epoch info.\n"
        "Run /help for all commands.",
    )


# ─── Error Handler ────────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception: {context.error}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is required.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("miners", cmd_miners))
    app.add_handler(CommandHandler("epoch", cmd_epoch))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cmd_help))
    app.add_error_handler(error_handler)

    logger.info("RustChain Telegram Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
