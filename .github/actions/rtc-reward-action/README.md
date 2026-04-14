# RTC Reward Action

> GitHub Action to automatically award RTC tokens when a Pull Request is merged.

**Bounty: 20 RTC** | Issue: [#2864](https://github.com/Scottcjn/rustchain-bounties/issues/2864)

## How It Works

When a PR is merged, this action transfers RTC from a project fund wallet to the PR author's wallet via the RustChain `/wallet/transfer` API.

## Usage

```yaml
name: RTC Reward

on:
  pull_request:
    types: [closed]

jobs:
  reward:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: Award RTC for merged PR
        uses: jujujuda/rtc-reward-action@v1
        with:
          node-url: https://50.28.86.131
          amount: 5
          wallet-from: your-project-fund
          admin-key: ${{ secrets.RTC_ADMIN_KEY }}
          recipient: ${{ github.event.pull_request.user.login }}
          memo: "PR merged — RTC reward"
```

## Setup Secrets

Add `RTC_ADMIN_KEY` in **Settings → Secrets and variables → Actions**.

## Configuration

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `node-url` | Yes | `https://50.28.86.131` | RustChain node URL |
| `amount` | Yes | — | RTC amount per merge |
| `wallet-from` | Yes | — | Sender wallet name |
| `admin-key` | Yes | — | Admin key for transfers |
| `recipient` | No | PR author | Recipient wallet |
| `memo` | No | `PR merged — RTC reward` | Transfer memo |

## Files

- `action.yml` — Action metadata
- `Dockerfile` — Container image
- `entrypoint.sh` — Entry point script  
- `src/reward.py` — Core transfer logic

## License

MIT
