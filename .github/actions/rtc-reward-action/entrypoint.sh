#!/bin/bash
set -e

NODE_URL="${1}"
AMOUNT="${2}"
WALLET_FROM="${3}"
ADMIN_KEY="${4}"
RECIPIENT="${5}"
MEMO="${6:-PR merged — RTC reward}"

# PR author is the recipient
if [ -z "$RECIPIENT" ]; then
  RECIPIENT="${GITHUB_ACTOR:-unknown}"
fi

echo "Awarding ${AMOUNT} RTC to ${RECIPIENT} on merge of ${GITHUB_REPOSITORY}"
echo "Node: ${NODE_URL}"

python3 /app/src/reward.py \
  --node-url "$NODE_URL" \
  --amount "$AMOUNT" \
  --wallet-from "$WALLET_FROM" \
  --admin-key "$ADMIN_KEY" \
  --recipient "$RECIPIENT" \
  --memo "$MEMO"
