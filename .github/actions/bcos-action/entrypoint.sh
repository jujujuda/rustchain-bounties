#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
#
# BCOS v2 GitHub Action — Entry Point
# Beacon Certified Open Source verification for any repository.
#
# Usage:
#   uses: Scottcjn/bcos-action@v1
#   with:
#     tier: L1          # L0 | L1 | L2
#     reviewer: ""      # human reviewer name for L2
#     node-url: ""      # RustChain node URL
#     repo-token: ""    # GitHub token (GITHUB_TOKEN)
#     post-comment: "true"
#
# Outputs:
#   trust_score  — BCOS score 0-100
#   cert_id      — BCOS-xxxxxxxx
#   tier_met     — true | false

set -euo pipefail

# ── Parse inputs ──────────────────────────────────────────────────────────────
TIER="${INPUT_TIER:-L1}"
REVIEWER="${INPUT_REVIEWER:-}"
NODE_URL="${INPUT_NODE_URL:-https://50.28.86.131}"
REPO_TOKEN="${INPUT_REPO_TOKEN:-${GITHUB_TOKEN:-}}"
POST_COMMENT="${INPUT_POST_COMMENT:-true}"

# Derived
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"
GITHUB_SHA="${GITHUB_SHA:-}"
GITHUB_EVENT_NAME="${GITHUB_EVENT_NAME:-}"
GITHUB_REF="${GITHUB_REF:-}"

echo "::group::BCOS v2 GitHub Action"
echo "BCOS Action: tier=$TIER reviewer=$REVIEWER"
echo "Repository: $GITHUB_REPOSITORY @ $GITHUB_SHA"
echo "Event: $GITHUB_EVENT_NAME"
echo "Node: $NODE_URL"
echo ""

# ── Outputs file ─────────────────────────────────────────────────────────────
OUTPUTS_FILE="${RUNNER_TEMP:-/tmp}/outputs.txt"
touch "$OUTPUTS_FILE"

set_output() {
    local name="$1"
    local value="$2"
    echo "${name}=${value}" >> "$OUTPUTS_FILE"
    echo "::set-output name=${name}::${value}"
}

# ── Clone BCOS engine ─────────────────────────────────────────────────────────
BCOS_DIR="/tmp/bcos-engine"
if [[ -d "$BCOS_DIR" ]]; then
    echo "Using cached BCOS engine"
else
    echo "::group::Cloning BCOS engine"
    git clone --depth=1 https://github.com/Scottcjn/Rustchain.git "$BCOS_DIR" 2>&1
    echo "::endgroup::"
fi

ENGINE="$BCOS_DIR/tools/bcos_engine.py"
if [[ ! -f "$ENGINE" ]]; then
    echo "ERROR: bcos_engine.py not found at $ENGINE"
    set_output trust_score "0"
    set_output cert_id "BCOS-ERROR"
    set_output tier_met "false"
    exit 1
fi

# ── Checkout PR branch ────────────────────────────────────────────────────────
REPO_DIR="/tmp/scan-repo"
if [[ -d "$REPO_DIR/.git" ]]; then
    echo "Using cached repo at $REPO_DIR"
else
    echo "::group::Cloning target repository"
    git clone --depth=1 "https://x-access-token:${REPO_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" "$REPO_DIR" 2>&1
    echo "::endgroup::"
fi

cd "$REPO_DIR"

# For PR events, fetch the PR branch
if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]] || [[ "$GITHUB_EVENT_NAME" == "pull_request_target" ]]; then
    PR_NUM="${PR_NUM:-$(echo "$GITHUB_REF" | grep -oP '(?<=refs\/pull\/)\d+')}"
    if [[ -n "$PR_NUM" ]]; then
        echo "Fetching PR #$PR_NUM branch"
        git fetch origin "pull/${PR_NUM}/head:pr-branch" 2>&1 || true
        git checkout pr-branch 2>&1 || true
    fi
fi

echo "Working directory: $(pwd)"
echo "Git log: $(git log --oneline -3)"

# ── Run BCOS scan ─────────────────────────────────────────────────────────────
echo ""
echo "::group::Running BCOS v2 scan (tier=$TIER)"

SCAN_OUTPUT="/tmp/bcos-report.json"

python3 "$ENGINE" \
    "$(pwd)" \
    --tier "$TIER" \
    --reviewer "$REVIEWER" \
    --json > "$SCAN_OUTPUT" 2>&1 || true

echo "::endgroup::"

# ── Parse results ─────────────────────────────────────────────────────────────
if [[ ! -f "$SCAN_OUTPUT" ]] || [[ ! -s "$(cat "$SCAN_OUTPUT")" ]]; then
    echo "ERROR: BCOS scan produced no output"
    set_output trust_score "0"
    set_output cert_id "BCOS-ERROR"
    set_output tier_met "false"
    exit 0
fi

TRUST_SCORE=$(python3 -c "import json; d=json.load(open('$SCAN_OUTPUT')); print(d.get('trust_score', 0))" 2>/dev/null || echo "0")
CERT_ID=$(python3 -c "import json; d=json.load(open('$SCAN_OUTPUT')); print(d.get('cert_id', 'BCOS-UNKNOWN'))" 2>/dev/null || echo "BCOS-UNKNOWN")
TIER_MET=$(python3 -c "import json; d=json.load(open('$SCAN_OUTPUT')); print('true' if d.get('tier_met', False) else 'false')" 2>/dev/null || echo "false")

echo ""
echo "BCOS Results:"
echo "  trust_score : $TRUST_SCORE"
echo "  cert_id     : $CERT_ID"
echo "  tier_met    : $TIER_MET"

set_output trust_score "$TRUST_SCORE"
set_output cert_id "$CERT_ID"
set_output tier_met "$TIER_MET"

# ── Format PR comment ─────────────────────────────────────────────────────────
build_comment() {
    local score="$1"
    local cert_id="$2"
    local tier_met="$3"

    local badge_color
    local badge_text
    if [[ "$tier_met" == "true" ]]; then
        badge_color="brightgreen"
        badge_text="✓ BCOS $TIER PASS"
    else
        badge_color="red"
        badge_text="✗ BCOS $TIER FAIL"
    fi

    # Score badge via shields.io
    local score_badge="![BCOS](https://img.shields.io/badge/BCOS-${score}%2F100-${badge_color})"
    local cert_badge="![Cert](https://img.shields.io/badge/${cert_id}-${badge_color})"

    cat << COMMENT
## 🛡️ BCOS v2 Scan Results

| Metric | Value |
|--------|-------|
| **Trust Score** | ${score} / 100 |
| **Certificate ID** | \`${cert_id}\` |
| **Tier** | ${TIER} |
| **Status** | ${badge_text} |
| **Engine** | BCOS v2 (MIT Licensed) |

$(
python3 -c "
import json
d = json.load(open('$SCAN_OUTPUT'))
breakdown = d.get('score_breakdown', {})
checks = d.get('checks', {})

print('### Score Breakdown')
print()
print('| Check | Score |')
print('|-------|-------|')
total = 0
for check, weight in {
    'license_compliance': 20,
    'vulnerability_scan': 25,
    'static_analysis': 20,
    'sbom_completeness': 10,
    'dependency_freshness': 5,
    'test_evidence': 10,
    'review_attestation': 10,
}.items():
    pts = breakdown.get(check, 0)
    total += pts
    status = '✅' if pts >= weight else '⚠️'
    print(f'| {check} | {pts}/{weight} {status} |')
print(f'| **TOTAL** | **{total}**/100 |')
print()
print('### Checks')
print()
for check_name, check_data in checks.items():
    result = check_data.get('result', 'unknown')
    msg = check_data.get('message', '')
    print(f'- **{check_name}**: {result} — {msg}')
" 2>/dev/null || true
)

---
*BCOS v2 — [rustchain.org/bcos](https://rustchain.org/bcos) — Powered by RustChain*
COMMENT
}

COMMENT=$(build_comment "$TRUST_SCORE" "$CERT_ID" "$TIER_MET")

# ── Post PR comment ───────────────────────────────────────────────────────────
if [[ "$POST_COMMENT" == "true" ]] && [[ -n "$REPO_TOKEN" ]]; then
    echo ""
    echo "::group::Posting PR comment"

    PR_NUM="${PR_NUM:-}"
    COMMENT_FILE="/tmp/pr-comment.txt"
    echo "$COMMENT" > "$COMMENT_FILE"

    if [[ -z "$PR_NUM" ]]; then
        # Try to get PR number from event
        if [[ -f "${GITHUB_EVENT_PATH:-}" ]]; then
            PR_NUM=$(python3 -c "import json; e=json.load(open('${GITHUB_EVENT_PATH}')); print(e.get('pull_request', {}).get('number', ''))" 2>/dev/null || echo "")
        fi
    fi

    if [[ -n "$PR_NUM" ]]; then
        RESP=$(curl -s -X POST \
            -H "Authorization: token $REPO_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/issues/${PR_NUM}/comments" \
            -d "$(python3 -c "import json; print(json.dumps({'body': open('$COMMENT_FILE').read()}))")")

        if echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if 'id' in d else 1)" 2>/dev/null; then
            echo "✅ PR comment posted successfully"
        else
            echo "⚠️ Could not post PR comment: $(echo "$RESP" | head -c 200)"
        fi
    else
        echo "⚠️ No PR number found, skipping comment"
    fi

    echo "::endgroup::"
fi

# ── Anchor on merge ───────────────────────────────────────────────────────────
if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]] || [[ "$GITHUB_EVENT_NAME" == "push" ]]; then
    # Check if this was a merge
    IS_MERGE=$(python3 -c "import json; e=json.load(open('${GITHUB_EVENT_PATH:-/dev/null}')); print('true' if e.get('pull_request', {}).get('merged', False) else 'false')" 2>/dev/null || echo "false")

    if [[ "$IS_MERGE" == "true" ]] || [[ "$GITHUB_EVENT_NAME" == "push" && "$GITHUB_SHA" != "" ]]; then
        echo ""
        echo "::group::Anchoring attestation to RustChain"

        ANCHOR_PAYLOAD=$(python3 -c "
import json, hashlib, datetime
d = json.load(open('$SCAN_OUTPUT'))
payload = {
    'cert_id': d.get('cert_id', '$CERT_ID'),
    'trust_score': d.get('trust_score', 0),
    'tier': d.get('tier', '$TIER'),
    'tier_met': d.get('tier_met', False),
    'commit_sha': d.get('commit_sha', '$GITHUB_SHA'),
    'repo': '$GITHUB_REPOSITORY',
    'timestamp': d.get('timestamp', datetime.datetime.now(datetime.timezone.utc).isoformat()),
}
print(json.dumps(payload, indent=2))
" 2>/dev/null)

        echo "Anchor payload:"
        echo "$ANCHOR_PAYLOAD"

        # Post to RustChain node
        ANCHOR_RESP=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            "${NODE_URL}/attest/submit" \
            -d "$ANCHOR_PAYLOAD" 2>/dev/null || echo '{"error":"node unreachable"}')

        echo "Anchor response: $ANCHOR_RESP"
        echo "::endgroup::"
    fi
fi

echo ""
echo "✅ BCOS v2 scan complete — score=$TRUST_SCORE cert_id=$CERT_ID tier_met=$TIER_MET"
echo "::endgroup::"
