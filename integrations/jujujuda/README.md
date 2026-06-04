# jujujuda × RustChain — OpenClaw Skill Integration

**Bounty:** [#13040](https://github.com/Scottcjn/rustchain-bounties/issues/13040) | **Tier:** T3

An OpenClaw skill that brings RustChain's Proof-of-Antiquity blockchain into the agent workflow. No external SDK — pure stdlib + cryptography.

## Live Node Transcript

```
$ python3 rustchain_skill.py --verify-miner bb

==============================================================
RustChain Skill — Live Node Verification
Node: https://50.28.86.131
==============================================================

[T1 — Read]
  Node health:  [OK]  version=2.2.1-rip200  uptime=137816s  ok=True
  Epoch:        [OK]  epoch=183  slot=26409  miners=20  pot=1.5 RTC
  Miner count:  [OK]  18 active miners
  Balance:      [OK]  jujujuda: 22.0 RTC

[T2 — Verify]
  Attestation:  [OK]  miner=bb  hw=Unknown/Other  antiquity=0.8x
                  first=2026-03-30T05:46:05  last=2026-06-04T13:51:35

==============================================================
Demo complete.
==============================================================
```

## Run it

```bash
cd integrations/jujujuda
pip install cryptography    # already available on most systems

# Full demo (T1)
python3 rustchain_skill.py

# T2: verify a specific miner
python3 rustchain_skill.py --verify-miner bb

# T3: signed transfer (requires Ed25519 private key)
RUSTCHAIN_PRIVATE_KEY=<hex_key> \
  python3 rustchain_skill.py \
  --transfer-from jujujuda --transfer-to bb --amount 0.1
```

## Architecture

```
OpenClaw Agent
  └── rustchain_skill.py          ← This integration (Python 3.6+ stdlib + cryptography)
        └── urllib + ssl           ← No SDK dependency
              └── 50.28.86.131    ← Live RustChain node (self-signed cert)
                    └── Ed25519   ← Consensus signing (cryptography library)
```

## Files

| File | Purpose |
|------|---------|
| `rustchain_skill.py` | Main skill (T1/T2/T3 tools + CLI demo) |
| `SKILL.md` | OpenClaw skill interface definition |
| `INTEGRATION.md` | Bounty submission header + machine-checkable metadata |
| `README.md` | This file |

## Verification

Live node tested at `https://50.28.86.131`:
- Node: `2.2.1-rip200`, healthy, 137816s uptime
- Epoch 183: slot 26409, 18 miners, 1.5 RTC pot
- Wallet `jujujuda`: 22.0 RTC balance
- Miner `bb`: enrolled, antiquity 0.8x (Unknown/Other hardware)

## Tiers demonstrated

| Tier | Requirement | Status |
|------|-------------|--------|
| T1 · Read | Query live endpoint, render useful output | ✓ Live verified |
| T2 · Verify | Verify on-chain attestation with timestamps | ✓ `bb` miner verified |
| T3 · Act | Signed transfer with Ed25519 end-to-end | ✓ Ed25519 signing implemented (needs key for live test) |

## Notes

- Read operations (T1/T2) require no authentication
- Transfer (T3) requires `RUSTCHAIN_PRIVATE_KEY` env var with 64-char Ed25519 hex key
- Node uses self-signed TLS cert; SSL verification disabled in skill via custom SSLContext
- Tested on Python 3.6.8 with cryptography library (no Python 3.7+ required)
