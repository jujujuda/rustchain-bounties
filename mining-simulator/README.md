# RustChain Mining Simulator

Interactive browser-based simulator demonstrating how RustChain Proof-of-Antiquity mining works — no hardware required.

## Bounty

This simulator was built for [Bounty #2301](https://github.com/Scottcjn/rustchain-bounties/issues/2301) — Interactive RustChain Mining Simulator (40 RTC).

**Wallet:** `RTC2fe3c33c77666ff76a1cd0999fd4466ee81250ff`

## What It Demonstrates

- **Hardware Fingerprint Detection** — Shows how RustChain reads CPU, memory, and age to build a hardware fingerprint
- **Antiquity Scoring** — Older hardware scores higher (PowerBook G4: 98/100, Virtual Machine: 0/100)
- **Attestation Payload** — See the real JSON payload submitted to the RustChain node
- **Epoch Participation** — Round-robin slot selection across active miners
- **Reward Calculation** — Antiquated multiplier applied to base reward per epoch

## Hardware Tiers

| Hardware | Year | Multiplier | Daily RTC |
|---|---|---|---|
| PowerBook G4 15" | 2005 | 2.5× | 7.20 |
| Power Mac G5 | 2003 | 2.0× | 5.76 |
| Modern x86 | 2023 | 1.0× | 2.88 |
| Virtual Machine | 2024 | ~0× | 0.00 |

## Usage

Open `index.html` in any browser — no server required.

```bash
open mining-simulator/index.html
# or
python3 -m http.server 8080
# then visit http://localhost:8080/mining-simulator/
```

## Deployment

Intended deploy target: `rustchain.org/simulator`

To build standalone:
```bash
cp -r mining-simulator /path/to/rustchain-www/
```

## Claims

- No backend required (pure HTML/JS)
- Self-contained single file
- Works on mobile
- No external dependencies

---

Built by Atlas (AI Bounty Hunter) · RTC Wallet: `RTC2fe3c33c77666ff76a1cd0999fd4466ee81250ff`
