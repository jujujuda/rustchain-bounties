#!/usr/bin/env python3
"""
RustChain Skill — OpenClaw Skill for RustChain Proof-of-Antiquity Blockchain
=============================================================================
T1: Query live node (health, epoch, miners, balance)
T2: Verify on-chain attestation for a miner  
T3: Execute signed RTC transfer with Ed25519

No external SDK dependency — stdlib + cryptography only.

Usage:
    python3 rustchain_skill.py [--verify-miner NAME]
    python3 rustchain_skill.py --transfer-from F --transfer-to T --amount N

Requirements:
    pip install cryptography   (already available on most systems)

Bounty: https://github.com/Scottcjn/rustchain-bounties/issues/13040
"""

from __future__ import print_function

import os
import sys
import json
import hashlib
import argparse
import ssl
import urllib.request
import urllib.error
import time

# ── Cryptography (Ed25519 signing) ────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: cryptography not installed. Run: pip install cryptography")
    sys.exit(1)

# ── SSL Context (self-signed cert on node) ────────────────────────────────────
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ── Configuration ──────────────────────────────────────────────────────────────
NODE_URL = os.environ.get("RUSTCHAIN_NODE_URL", "https://50.28.86.131")
WALLET_ID = os.environ.get("RUSTCHAIN_WALLET_ID", "jujujuda")
PRIVATE_KEY_HEX = os.environ.get("RUSTCHAIN_PRIVATE_KEY", "")


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _api_get(path, params=None):
    url = NODE_URL + path
    if params:
        url += "?" + "&".join("{0}={1}".format(k, v) for k, v in params.items())
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"error": "HTTP {0}: {1}".format(e.code, e.reason)}
    except Exception as e:
        return {"error": str(e)}


def _api_post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        NODE_URL + path, data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"error": "HTTP {0}: {1}".format(e.code, e.reason)}
    except Exception as e:
        return {"error": str(e)}


# ── Skill Tools ────────────────────────────────────────────────────────────────

def rustchain_health():
    """T1 — Check node health, version, uptime."""
    data = _api_get("/health")
    if "error" in data:
        return data
    return {
        "ok": data.get("ok", False),
        "version": data.get("version", "unknown"),
        "uptime_s": round(data.get("uptime_s", 0), 1),
        "db_rw": data.get("db_rw", False),
        "tip_age_slots": data.get("tip_age_slots", -1),
    }


def rustchain_epoch():
    """T1 — Get current epoch info."""
    data = _api_get("/epoch")
    if "error" in data:
        return data
    return {
        "epoch": data.get("epoch", 0),
        "slot": data.get("slot", 0),
        "blocks_per_epoch": data.get("blocks_per_epoch", 0),
        "enrolled_miners": data.get("enrolled_miners", 0),
        "epoch_pot": data.get("epoch_pot", 0.0),
        "total_supply_rtc": data.get("total_supply_rtc", 0),
    }


def rustchain_miners(limit=20):
    """T1 — List enrolled miners."""
    data = _api_get("/api/miners")
    if "error" in data:
        return data
    return [
        {
            "miner": m.get("miner", ""),
            "hardware_type": m.get("hardware_type", ""),
            "device_family": m.get("device_family", ""),
            "antiquity_multiplier": m.get("antiquity_multiplier", 0.0),
            "last_attest": m.get("last_attest"),
        }
        for m in data.get("miners", [])[:limit]
    ]


def rustchain_balance(wallet_id):
    """T1 — Check RTC balance for any wallet."""
    return _api_get("/wallet/balance", params={"miner_id": wallet_id})


def rustchain_verify_attestation(miner_id):
    """
    T2 — Verify a miner's on-chain attestation.
    
    Checks miner exists in registry, has first_attest timestamp,
    and antiquity_multiplier reflects real hardware age.
    """
    data = _api_get("/api/miners")
    if "error" in data:
        return data
    
    miner = None
    for m in data.get("miners", []):
        if m.get("miner") == miner_id:
            miner = m
            break
    
    if not miner:
        return {"verified": False, "reason": "Miner '{0}' not found in registry".format(miner_id)}
    
    from datetime import datetime
    first_attest = miner.get("first_attest")
    last_attest = miner.get("last_attest")
    first_dt = datetime.fromtimestamp(first_attest).isoformat() if first_attest else None
    last_dt = datetime.fromtimestamp(last_attest).isoformat() if last_attest else None
    
    return {
        "verified": first_attest is not None,
        "miner_id": miner.get("miner"),
        "hardware_type": miner.get("hardware_type"),
        "device_arch": miner.get("device_arch"),
        "antiquity_multiplier": miner.get("antiquity_multiplier"),
        "first_attest": first_attest,
        "first_attest_datetime": first_dt,
        "last_attest": last_attest,
        "last_attest_datetime": last_dt,
        "entropy_score": miner.get("entropy_score"),
    }


def _build_transfer_payload(from_w, to_w, amount, nonce):
    """Canonical payload for Ed25519 signing: from:to:amount:nonce"""
    return "{0}:{1}:{2}:{3}".format(from_w, to_w, amount, nonce).encode("utf-8")


def _get_nonce(from_wallet):
    """Get transfer nonce. Falls back to deterministic hash-based nonce."""
    data = _api_get("/wallet/nonce", params={"miner_id": from_wallet})
    if "error" not in data and "nonce" in data:
        return int(data["nonce"])
    base = int(hashlib.sha256(from_wallet.encode()).hexdigest()[:8], 16) % 1000000
    return base + int(time.time()) % 1000


def rustchain_transfer_signed(from_wallet, to_wallet, amount):
    """
    T3 — Execute signed RTC transfer end-to-end with Ed25519.
    
    Requires RUSTCHAIN_PRIVATE_KEY env var (Ed25519 hex, 64 chars).
    """
    if not PRIVATE_KEY_HEX:
        return {"error": "RUSTCHAIN_PRIVATE_KEY env var not set",
                "hint": "Ed25519 private key hex (64 chars)"}
    
    try:
        pk_bytes = bytes.fromhex(PRIVATE_KEY_HEX)
        private_key = Ed25519PrivateKey.from_private_bytes(pk_bytes)
        public_key = private_key.public_key()
        pub_bytes = public_key.public_bytes(
            serialization.Encoding.raw,
            serialization.PublicFormat.Raw
        )
    except Exception as e:
        return {"error": "Invalid private key: " + str(e),
                "hint": "Provide 64-char hex Ed25519 key"}
    
    nonce = _get_nonce(from_wallet)
    payload = _build_transfer_payload(from_wallet, to_wallet, amount, nonce)
    sig = private_key.sign(payload)
    sig_hex = sig.hex()
    pub_hex = pub_bytes.hex()
    
    result = _api_post("/wallet/transfer/signed", {
        "from": from_wallet,
        "to": to_wallet,
        "amount": amount,
        "nonce": nonce,
        "signature": sig_hex,
        "public_key": pub_hex,
    })
    
    if "error" in result:
        return {
            "error": result.get("error"),
            "details": result,
            "signature": sig_hex[:16] + "...",
            "nonce": nonce,
        }
    
    return {
        "success": result.get("success", False),
        "tx_hash": result.get("tx_hash", "n/a"),
        "message": result.get("message", ""),
        "amount": result.get("amount", amount),
        "from": result.get("from_wallet", from_wallet),
        "to": result.get("to_wallet", to_wallet),
        "signature": sig_hex[:16] + "...",
        "nonce": nonce,
    }


# ── OpenClaw Skill Interface ──────────────────────────────────────────────────

SKILL_TOOLS = {
    "rustchain_health": {
        "fn": rustchain_health,
        "description": "Check node health, version, uptime. No auth. T1.",
        "parameters": {},
    },
    "rustchain_epoch": {
        "fn": rustchain_epoch,
        "description": "Get current epoch/slot/miners/pot. No auth. T1.",
        "parameters": {},
    },
    "rustchain_miners": {
        "fn": rustchain_miners,
        "description": "List enrolled miners with hardware/antiquity. T1.",
        "parameters": {"limit": {"type": "int", "default": 20}},
    },
    "rustchain_balance": {
        "fn": rustchain_balance,
        "description": "Check RTC balance for any wallet. T1.",
        "parameters": {"wallet_id": {"type": "str"}},
    },
    "rustchain_verify_attestation": {
        "fn": rustchain_verify_attestation,
        "description": "Verify miner on-chain attestation. T2.",
        "parameters": {"miner_id": {"type": "str"}},
    },
    "rustchain_transfer_signed": {
        "fn": rustchain_transfer_signed,
        "description": "Execute signed RTC transfer. Needs RUSTCHAIN_PRIVATE_KEY. T3.",
        "parameters": {
            "from_wallet": {"type": "str"},
            "to_wallet": {"type": "str"},
            "amount": {"type": "float"},
        },
    },
}


# ── CLI Demo ──────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="RustChain Skill — Live Demo")
    p.add_argument("--verify-miner", metavar="NAME", help="Verify miner (T2)")
    p.add_argument("--transfer-from", metavar="F", help="Transfer from (T3)")
    p.add_argument("--transfer-to", metavar="T", help="Transfer to (T3)")
    p.add_argument("--amount", type=float, metavar="N", help="Amount (T3)")
    args = p.parse_args()

    print("=" * 60)
    print("RustChain Skill — Live Node Verification")
    print("Node: {0}".format(NODE_URL))
    print("=" * 60)

    print("\n[T1 — Read]")
    r = rustchain_health()
    s = "OK" if "error" not in r else "ERR"
    print("  Node health:  [{0}]  version={1}  uptime={2}s  ok={3}".format(
        s, r.get("version","?"), r.get("uptime_s","?"), r.get("ok","?")))

    r = rustchain_epoch()
    s = "OK" if "error" not in r else "ERR"
    print("  Epoch:        [{0}]  epoch={1}  slot={2}  miners={3}  pot={4} RTC".format(
        s, r.get("epoch","?"), r.get("slot","?"), r.get("enrolled_miners","?"), r.get("epoch_pot","?")))

    r = rustchain_miners()
    s = "OK" if "error" not in r else "ERR"
    cnt = len(r) if isinstance(r, list) else "?"
    print("  Miner count:  [{0}]  {1} active miners".format(s, cnt))

    r = rustchain_balance(WALLET_ID)
    s = "OK" if "error" not in r else "ERR"
    print("  Balance:      [{0}]  {1}: {2} RTC".format(
        s, r.get("miner_id", WALLET_ID), r.get("amount_rtc", "?")))

    if args.verify_miner:
        print("\n[T2 — Verify]")
        r = rustchain_verify_attestation(args.verify_miner)
        if r.get("verified"):
            print("  Attestation:  [OK]  miner={0}  hw={1}  antiquity={2}x".format(
                r["miner_id"], r["hardware_type"], r["antiquity_multiplier"]))
            print("                  first={0}  last={1}".format(
                r.get("first_attest_datetime","?"), r.get("last_attest_datetime","?")))
        else:
            print("  Attestation:  [ERR] {0}".format(r.get("reason", "unknown")))

    if args.transfer_from and args.transfer_to and args.amount:
        print("\n[T3 — Signed Transfer]")
        if not PRIVATE_KEY_HEX:
            print("  Transfer:     [ERR] RUSTCHAIN_PRIVATE_KEY not set")
        else:
            r = rustchain_transfer_signed(args.transfer_from, args.transfer_to, args.amount)
            if "error" in r and not r.get("success"):
                print("  Transfer:     [ERR] {0}".format(r.get("error")))
            else:
                print("  Transfer:     [OK]  {0} RTC -> {1}  tx={2}".format(
                    r.get("amount"), r.get("to"), str(r.get("tx_hash","?"))[:16]))
                print("                  sig={0}  nonce={1}".format(
                    r.get("signature","?"), r.get("nonce","?")))

    print("\n" + "=" * 60)
    print("Demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
