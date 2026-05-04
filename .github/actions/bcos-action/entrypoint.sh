#!/bin/bash
set -euo pipefail

echo "BCOS v2 GitHub Action starting..."
echo "GitHub workspace: ${GITHUB_WORKSPACE:-/github/workspace}"

TIER="${1:-L1}"
REVIEWER="${2:-}"
NODE_URL="${3:-https://rustchain.org}"
FAIL_ON="${4:-l0}"
GITHUB_TOKEN="${5:-}"

echo "  tier: $TIER"
echo "  reviewer: $REVIEWER"
echo "  node_url: $NODE_URL"
echo "  fail_on: $FAIL_ON"

WORKSPACE="${GITHUB_WORKSPACE:-/github/workspace}"

# Change to the workspace
cd "$WORKSPACE"
REPO_DIR="$WORKSPACE"

echo ""
echo "=== Downloading BCOS engine from Rustchain ==="
BCOS_ENGINE="/tmp/bcos_engine.py"
curl -sL "https://raw.githubusercontent.com/Scottcjn/Rustchain/main/tools/bcos_engine.py" \
    -o "$BCOS_ENGINE"
if [ ! -s "$BCOS_ENGINE" ]; then
    echo "ERROR: Failed to download bcos_engine.py"
    exit 1
fi
echo "BCOS engine downloaded ($(wc -l < "$BCOS_ENGINE") lines)"

# Get the commit SHA
COMMIT_SHA="${GITHUB_SHA:-$(git rev-parse HEAD 2>/dev/null || echo 'unknown')}"
echo "Scanning commit: $COMMIT_SHA"

echo ""
echo "=== Running BCOS v2 scan ==="
SCAN_OUTPUT=$(python3 "$BCOS_ENGINE" "$REPO_DIR" \
    --tier "$TIER" \
    --reviewer "$REVIEWER" \
    --commit "$COMMIT_SHA" \
    --json 2>&1) || true

echo "Scan output received (${#SCAN_OUTPUT} chars)"

# Extract JSON from output
REPORT_JSON=$(echo "$SCAN_OUTPUT" | grep -oP '\{[^}]*"trust_score"[^}]*\}' | tail -1 || echo '{}')

TRUST_SCORE=$(echo "$REPORT_JSON" | jq -r '.trust_score // 0')
TIER_MET=$(echo "$REPORT_JSON" | jq -r 'if .tier_met then "true" else "false" end')
TIER_ACHIEVED=$(echo "$REPORT_JSON" | jq -r '.tier_achieved // "L0"')
CERT_ID=$(echo "$REPORT_JSON" | jq -r '.cert_id // ""')

echo ""
echo "=== BCOS Results ==="
echo "trust_score=$TRUST_SCORE"
echo "tier_met=$TIER_MET"
echo "tier_achieved=$TIER_ACHIEVED"
echo "cert_id=$CERT_ID"

# Set GitHub Actions outputs
echo "::set-output name=trust_score::$TRUST_SCORE"
echo "::set-output name=tier_met::$TIER_MET"
echo "::set-output name=tier_achieved::$TIER_ACHIEVED"
echo "::set-output name=cert_id::$CERT_ID"
# Escape JSON for output
ESCAPED_JSON=$(echo "$REPORT_JSON" | jq -c . | sed 's/%/%%/g')
echo "::set-output name=report_json::$ESCAPED_JSON"

echo ""
echo "=== Posting PR Comment ==="
if [ -n "$GITHUB_TOKEN" ] && [ -n "${GITHUB_PR_NUMBER:-}" ]; then
    PR_NUMBER="$GITHUB_PR_NUMBER"
    REPO="${GITHUB_REPOSITORY:-}"
    OWNER="${REPO%%/*}"
    REPO_NAME="${REPO##*/}"
    
    # Build badge URL
    BADGE_URL="https://img.shields.io/badge/BCOS-${TIER_ACHIEVED}-${TRUST_SCORE}%2F100-brightgreen"
    
    # Extract check details
    CHECKS=$(echo "$REPORT_JSON" | jq -c '.checks // {}')
    LIC_SCORE=$(echo "$CHECKS" | jq -r '.license_compliance.score // 0')
    VULN_SCORE=$(echo "$CHECKS" | jq -r '.vulnerability_scan.score // 0')
    STATIC_SCORE=$(echo "$CHECKS" | jq -r '.static_analysis.score // 0')
    SBOM_SCORE=$(echo "$CHECKS" | jq -r '.sbom_completeness.score // 0')
    DEPS_SCORE=$(echo "$CHECKS" | jq -r '.dependency_freshness.score // 0')
    TEST_SCORE=$(echo "$CHECKS" | jq -r '.test_evidence.score // 0')
    REVIEW_SCORE=$(echo "$CHECKS" | jq -r '.review_attestation.score // 0')
    
    TIER_CHECK=$([ "$TIER_MET" = "true" ] && echo "✅" || echo "❌")
    
    COMMENT_BODY=$(cat <<TEMPLATE
## 🛡️ BCOS v2 Scan Results

| | |
|---|---|
| **Trust Score** | **${TRUST_SCORE}/100** $TIER_CHECK |
| **Tier Claimed** | $TIER |
| **Tier Achieved** | $TIER_ACHIEVED |

### Score Breakdown

| Dimension | Score |
|-----------|-------|
| License Compliance | $LIC_SCORE/20 |
| Vulnerability Scan | $VULN_SCORE/25 |
| Static Analysis | $STATIC_SCORE/20 |
| SBOM Completeness | $SBOM_SCORE/10 |
| Dependency Freshness | $DEPS_SCORE/5 |
| Test Evidence | $TEST_SCORE/10 |
| Review Attestation | $REVIEW_SCORE/10 |

**Certificate ID:** \`${CERT_ID}\`
**Commit:** \`${COMMIT_SHA}\`
**Reviewer:** ${REVIEWER:-_not specified_}

> 🔍 [Verify on rustchain.org/bcos](${NODE_URL}/bcos/verify/${CERT_ID})
> 📋 [BCOS v2 Spec](https://github.com/Scottcjn/Rustchain/blob/main/docs/BEACON_CERTIFIED_OPEN_SOURCE.md)

*BCOS v2 — beacon-certified open source. Powered by RustChain.*
TEMPLATE
)
    
    RESPONSE=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$OWNER/$REPO_NAME/issues/$PR_NUMBER/comments" \
        -d "$(jq -n --arg body "$COMMENT_BODY" '{body: $body}')")
    
    if echo "$RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
        echo "PR comment posted successfully."
    else
        echo "Warning: Could not post PR comment: $RESPONSE"
    fi
else
    echo "Skipping PR comment (no token or PR number)."
fi

echo ""
echo "=== Determining pass/fail ==="
FAIL_SCORE=0
[ "$FAIL_ON" = "l1" ] && FAIL_SCORE=60
[ "$FAIL_ON" = "l2" ] && FAIL_SCORE=80

if [ "$TRUST_SCORE" -lt "$FAIL_SCORE" ]; then
    echo "FAIL: BCOS score $TRUST_SCORE < minimum $FAIL_SCORE for tier ${FAIL_ON^^}"
    exit 1
else
    echo "PASS: BCOS score $TRUST_SCORE meets threshold $FAIL_SCORE"
    exit 0
fi
