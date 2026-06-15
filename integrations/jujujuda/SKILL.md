# RustChain Skill

Interact with the RustChain Proof-of-Antiquity blockchain directly from OpenClaw.

## Tools

### `rustchain_health`
Check node health, version, and uptime.
- **Auth:** None
- **Returns:** `{ok, version, uptime_s, db_rw, tip_age_slots}`

### `rustchain_epoch`
Get current epoch info.
- **Auth:** None
- **Returns:** `{epoch, slot, blocks_per_epoch, enrolled_miners, epoch_pot, total_supply_rtc}`

### `rustchain_miners(limit=20)`
List enrolled miners.
- **Auth:** None
- **Returns:** List of `{miner, hardware_type, antiquity_multiplier, last_attest}`

### `rustchain_balance(wallet_id)`
Check RTC balance for any wallet.
- **Auth:** None
- **Returns:** `{miner_id, amount_rtc, amount_i64}`

### `rustchain_verify_attestation(miner_id)`
Verify a miner's on-chain attestation (T2).
- **Auth:** None
- **Returns:** `{verified, miner_id, hardware_type, antiquity_multiplier, first_attest_datetime, last_attest_datetime}`

### `rustchain_transfer_signed(from_wallet, to_wallet, amount)`
Execute a signed RTC transfer end-to-end (T3).
- **Auth:** `RUSTCHAIN_PRIVATE_KEY` env var (Ed25519 hex)
- **Returns:** `{success, tx_hash, amount, from, to, signature, nonce}`

## Configuration

```env
RUSTCHAIN_NODE_URL=https://50.28.86.131  # optional
RUSTCHAIN_WALLET_ID=jujujuda              # optional, default wallet
RUSTCHAIN_PRIVATE_KEY=...                 # Ed25519 hex, for transfers only
```

## Installation

```bash
pip install rustchain cryptography
```

## Usage

```python
from rustchain_skill import (
    rustchain_health,
    rustchain_epoch,
    rustchain_miners,
    rustchain_balance,
    rustchain_verify_attestation,
    rustchain_transfer_signed,
)

# T1 — Read
health = rustchain_health()
print(health["version"])

epoch = rustchain_epoch()
print(f"Epoch {epoch['epoch']}, {epoch['enrolled_miners']} miners")

# T2 — Verify
att = rustchain_verify_attestation("jujujuda")
print(f"Verified: {att['verified']}, antiquity: {att['antiquity_multiplier']}x")

# T3 — Transfer (needs RUSTCHAIN_PRIVATE_KEY)
result = rustchain_transfer_signed("wallet_a", "wallet_b", 1.0)
print(result["success"])
```
