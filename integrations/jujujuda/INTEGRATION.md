```
tier: T3
target: rustchain
language: python
endpoints_used: [/health, /epoch, /api/miners, /wallet/balance, /wallet/transfer/signed]
wallet: RTCjujujuda
starred: yes
```

# RustChain Skill Integration — jujujuda

**Bounty:** [#13040](https://github.com/Scottcjn/rustchain-bounties/issues/13040) (10–40 RTC by tier, 500 RTC pool)

## What is this

An OpenClaw skill that brings RustChain's Proof-of-Antiquity blockchain directly into the agent workflow. Query live node state, verify on-chain attestations, and execute signed RTC transfers — all from natural language or CLI.

**No external SDK dependency** — uses only Python 3.6 stdlib (`urllib`, `ssl`, `json`) + `cryptography` for Ed25519 signing.

## Live transcript (verified against live node 50.28.86.131)

```
$ python3 rustchain_skill.py --verify-miner bb

[T1 — Read]
  Node health:  [OK]  version=2.2.1-rip200  uptime=137816s  ok=True
  Epoch:        [OK]  epoch=183  slot=26409  miners=20  pot=1.5 RTC
  Miner count:  [OK]  18 active miners
  Balance:      [OK]  jujujuda: 22.0 RTC

[T2 — Verify]
  Attestation:  [OK]  miner=bb  hw=Unknown/Other  antiquity=0.8x
                  first=2026-03-30T05:46:05  last=2026-06-04T13:51:35
```

## Run it

```bash
pip install cryptography
cd integrations/jujujuda
python3 rustchain_skill.py                    # T1 demo
python3 rustchain_skill.py --verify-miner bb # T2 demo
```

## Tools provided

| Tool | Tier | Description |
|------|------|-------------|
| `rustchain_health` | T1 | Node health/version/uptime |
| `rustchain_epoch` | T1 | Epoch/slot/miner count/pot |
| `rustchain_miners` | T1 | List miners with hardware info |
| `rustchain_balance` | T1 | Wallet RTC balance |
| `rustchain_verify_attestation` | T2 | On-chain attestation verification |
| `rustchain_transfer_signed` | T3 | Ed25519-signed RTC transfer |
