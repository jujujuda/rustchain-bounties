# BCOS v2 GitHub Action

Run a [Beacon Certified Open Source (BCOS) v2](https://rustchain.org/bcos) trust scan on any repository directly from GitHub Actions.

## What It Does

1. Runs `bcos_engine.py` against the repository at the triggering commit
2. Produces a trust score (0-100) across 7 dimensions:
   - License Compliance (SPDX headers + dependency licenses) — 20 pts
   - Vulnerability Scan (critical/high CVEs) — 25 pts
   - Static Analysis (semgrep) — 20 pts
   - SBOM Completeness (CycloneDX) — 10 pts
   - Dependency Freshness — 5 pts
   - Test Evidence — 10 pts
   - Review Attestation — 10 pts
3. Determines tier achievement (L0 ≥ 40, L1 ≥ 60, L2 ≥ 80)
4. Posts a PR comment with the full score breakdown and badge
5. Sets GitHub Actions outputs for use in downstream steps

## Usage

```yaml
name: BCOS Scan

on:
  pull_request:
  workflow_dispatch:

jobs:
  bcos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: BCOS v2 Scan
        uses: Scottcjn/rustchain-bounties/.github/actions/bcos-action@v1
        with:
          tier: L1              # L0, L1, or L2
          reviewer: ''          # Beacon identity name (required for L2)
          node-url: https://rustchain.org
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          fail-on: l0           # fail workflow if below this tier
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `tier` | No | `L1` | Scan tier — L0 (automation), L1 (agent review), L2 (human review) |
| `reviewer` | No | — | Beacon identity name for attestation (required for L2) |
| `node-url` | No | `https://rustchain.org` | RustChain node for attestation anchoring |
| `repo-token` | **Yes** | — | GitHub token (use `${{ secrets.GITHUB_TOKEN }}`) |
| `fail-on` | No | `l0` | Fail workflow when score is below — `never`, `l0`, `l1`, `l2` |

## Outputs

| Output | Description |
|--------|-------------|
| `trust_score` | Overall BCOS trust score (0-100) |
| `tier_met` | Whether the requested tier was met (`true` / `false`) |
| `cert_id` | BCOS certificate ID (commit-based BLAKE2b hash) |
| `tier_achieved` | Highest tier achieved — L0, L1, or L2 |
| `report_json` | Full JSON report with per-dimension scores |

## Tiers

| Tier | Min Score | Requirement |
|------|-----------|-------------|
| L0 | 40 | Automated checks only |
| L1 | 60 | Automated checks + agent review evidence |
| L2 | 80 | Automated checks + agent review evidence + human approval |

## Example Badge

```
[![BCOS v2](https://img.shields.io/badge/BCOS-L1-78%2F100-brightgreen)](https://rustchain.org/bcos)
```

## License

MIT — [RustChain / Elyan Labs](https://github.com/Scottcjn/Rustchain)
