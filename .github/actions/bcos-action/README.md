# BCOS v2 GitHub Action

Beacon Certified Open Source — run a BCOS v2 trust scan on any repository.

## Usage

```yaml
name: BCOS v2 Scan

on:
  pull_request:
  push:
    branches: [main, master]

jobs:
  bcos-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: Scottcjn/bcos-action@v1
        with:
          tier: L1                    # L0 | L1 | L2
          reviewer: ""                # human reviewer name (required for L2)
          node-url: "https://50.28.86.131"  # RustChain node
          post-comment: "true"
```

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `tier` | BCOS tier to evaluate (L0, L1, L2) | `L1` |
| `reviewer` | Human reviewer name (for L1/L2 attestation) | `""` |
| `node-url` | RustChain node URL for attestation anchoring | `https://50.28.86.131` |
| `post-comment` | Post results as PR comment | `true` |
| `repo-token` | GitHub token (automatically provided via `GITHUB_TOKEN`) | `${{ github.token }}` |

## Outputs

| Output | Description |
|--------|-------------|
| `trust_score` | BCOS trust score (0–100) |
| `cert_id` | Certificate ID (`BCOS-xxxxxxxx`) |
| `tier_met` | Whether the tier threshold was met (`true`/`false`) |

## BCOS Trust Score (0–100)

| Check | Max Points |
|-------|-----------|
| License compliance (SPDX + OSI deps) | 20 |
| Vulnerability scan (CVEs) | 25 |
| Static analysis (semgrep) | 20 |
| SBOM completeness (CycloneDX) | 10 |
| Dependency freshness | 5 |
| Test evidence | 10 |
| Review attestation | 10 |

**Tier thresholds:** L0 ≥ 40, L1 ≥ 60, L2 ≥ 80 + human Ed25519 signature.

## Examples

### Basic L1 scan
```yaml
- uses: Scottcjn/bcos-action@v1
```

### L2 scan with reviewer
```yaml
- uses: Scottcjn/bcos-action@v1
  with:
    tier: L2
    reviewer: scott
```

### Skip PR comment
```yaml
- uses: Scottcjn/bcos-action@v1
  with:
    post-comment: "false"
```

## License

MIT — see [rustchain.org/bcos](https://rustchain.org/bcos)
