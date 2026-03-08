# RustChain MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with the RustChain blockchain directly from Claude Code, Claude Desktop, or any MCP-compatible client.

## Features

This MCP server provides the following tools:

| Tool | Description |
|------|-------------|
| `rustchain_balance` | Check RTC balance for any wallet |
| `rustchain_miners` | List active miners and their architectures |
| `rustchain_epoch` | Get current epoch info (slot, height, rewards) |
| `rustchain_health` | Check node health across all attestation nodes |
| `rustchain_transfer` | Send RTC (requires wallet key) |
| `rustchain_ledger` | Query transaction history (bonus) |
| `rustchain_register_wallet` | Create a new wallet (bonus) |
| `rustchain_bounties` | List open bounties with rewards (bonus) |

## Installation

### Prerequisites

- Python 3.10+
- `mcp` package
- `requests` package

### Install Dependencies

```bash
pip install mcp requests
```

### Add to Claude Code

```bash
claude mcp add rustchain-mcp-server python /path/to/rustchain_mcp_server.py
```

Or add manually to your Claude Code settings:

```json
{
  "mcpServers": {
    "rustchain-mcp-server": {
      "command": "python",
      "args": ["/path/to/rustchain_mcp_server.py"]
    }
  }
}
```

## Usage

Once installed, you can use the tools in your conversations with Claude:

### Check your balance
```
Check the RTC balance for wallet "mywallet"
```

### List miners
```
Who are the current active miners on RustChain?
```

### Check epoch
```
What's the current epoch info?
```

### Check node health
```
Is the RustChain node healthy?
```

### Transfer RTC
```
Transfer 10 RTC from mywallet to recipient_wallet
```

## Configuration

The server connects to the RustChain primary node by default. You can modify the `NODES` list in the code to add backup nodes:

```python
NODES = [
    "https://50.28.86.131",  # Primary
    "https://node2.example.com",  # Backup 1
    "https://node3.example.com",  # Backup 2
]
```

## API Endpoints

The server uses the following RustChain node API endpoints:

- `GET /health` - Node health check
- `GET /api/miners` - List active miners
- `GET /epoch` - Current epoch info
- `GET /wallet/balance?miner_id=WALLET` - Check balance
- `POST /wallet/transfer` - Send RTC
- `GET /wallet/ledger` - Transaction history
- `GET /wallet/register` - Create wallet
- `GET /api/bounties` - List bounties

## Development

### Run locally for testing

```bash
python rustchain_mcp_server.py
```

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python rustchain_mcp_server.py
```

## License

MIT
