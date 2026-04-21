# RustChain Telegram Bot — @RustChainBot

A Telegram bot that lets users check RustChain wallet balances, active miners, and epoch info directly from chat.

**Bounty:** [Issue #2869](https://github.com/Scottcjn/rustchain-bounties/issues/2869) — 10 RTC

---

## Commands

| Command | Description |
|---------|-------------|
| `/balance <wallet>` | Check RTC balance for a wallet/miner_id |
| `/miners` | List active miners on the network |
| `/epoch` | Current epoch, slot, block height, and rewards |
| `/price` | RTC internal reference rate ($0.10 USD) |
| `/help` | Show all commands |
| `/start` | Welcome message |

---

## Features

- **Rate limiting** — 1 request per user every 5 seconds (prevents spam)
- **Fallback nodes** — automatically retries on a secondary node if the primary is down
- **Error handling** — clear user-facing messages when the node is offline
- **Markdown output** — formatted replies for readability

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
export BOT_TOKEN="your-telegram-bot-token-from-@BotFather"
export NODE_URL="https://50.28.86.131"        # primary node
export FALLBACK_NODE="https://50.28.86.132"   # secondary node (optional)
```

### 3. Run

```bash
python bot.py
```

---

## Deployment

### systemd (recommended for self-hosting)

```ini
# /etc/systemd/system/rustchain-bot.service
[Unit]
Description=RustChain Telegram Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/rustchain-telegram-bot
ExecStart=/usr/bin/python3 bot.py
Restart=on-failure
RestartSec=10
Environment=BOT_TOKEN=your-token-here

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now rustchain-bot
```

### Railway

1. Connect your GitHub repo to [Railway](https://railway.app)
2. Add the `BOT_TOKEN` environment variable
3. Set the start command: `python telegram-bot/bot.py`

### Fly.io

```bash
fly launch
fly secrets set BOT_TOKEN=your-token-here
fly deploy
```

---

## Architecture

```
bot.py
├── Command handlers  — /balance, /miners, /epoch, /price, /help
├── Rate limiter      — per-user request throttling
├── Node health check — tries primary then fallback
└── API helpers       — fetch_balance, fetch_miners, fetch_epoch
```

**API Endpoints used:**

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Node health check |
| `GET /wallet/balance?miner_id=<wallet>` | Wallet balance |
| `GET /api/miners` | Active miners list |
| `GET /epoch` | Current epoch info |

---

## Bounty Payment Wallet

`RTC2fe3c33c77666ff76a1cd0999fd4466ee81250ff`

---

## License

MIT — see [rustchain-bounties](../README.md)
