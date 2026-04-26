# RustChain Dashboard — VS Code Extension

VS Code extension showing your RustChain wallet balance, miner status, epoch countdown, and an interactive bounty board.

## Features

- **Status Bar — Wallet Balance**: Shows your RTC balance in the VS Code status bar. Click to open in block explorer.
- **Status Bar — Miner Status**: Quick miner health indicator.
- **Status Bar — Epoch Timer**: Countdown to next epoch settlement.
- **Bounty Board (Sidebar)**: Browse all open bounties from the rustchain-bounties repo. Click any bounty to open it in your browser.

## Setup

1. Open VS Code Settings (`Ctrl+,` or `Cmd+,`)
2. Search for `rustchain`
3. Set your **Wallet Name** (your `miner_id` on RustChain)
4. Optionally customize the **Node URL** and **Refresh Interval**

## Requirements

- VS Code 1.75.0 or later
- Internet connection (to reach RustChain nodes and GitHub API)

## Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `rustchain.walletName` | (empty) | Your RustChain wallet name / miner_id |
| `rustchain.nodeUrl` | `https://50.28.86.131` | RustChain node URL |
| `rustchain.refreshInterval` | `60` | Refresh interval in seconds |

## API Endpoints Used

- `GET /wallet/balance?miner_id=<name>` — wallet balance
- `GET /epoch` — current epoch info
- `GET /api/miners` — miner list
- `GET /health` — node health

## Commands

- `RustChain: Refresh Data` — manually trigger a refresh of all status bar items
- Click any bounty in the sidebar to open it in GitHub

## Publishing

This extension can be packaged with `vsce package --yarn` and published to the VS Code Marketplace. Publisher: `jujujuda`.

## License

MIT
