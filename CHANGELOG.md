# Changelog

## Unreleased (development/m0-ux-eval)
- MIT license selected (`LICENSE`); packaging metadata (`pyproject.toml`).
- CI: Windows+Ubuntu × Python 3.11–3.14, four unittest suites, R3 archive
  verification, stdlib frontmatter validation, no-cache/secret/unsafe-member
  checks (`.github/`).
- `SECURITY.md`, `CONTRIBUTING.md` added.
- `docs/STATUS.md`: corrected R4 file inventory (five modified + five new).
- Reference routing: `references/INDEX.md` in both packages with explicit
  "read this when" rows, linked from each SKILL.md appendix.

## R3 / 2.0.0-m11 (main)
- Verified offline pair, 383 portable tests green, TEST_ONLY.
- Four Beads-inspired offline policies; native writes disabled.

## R4 native-observation candidate (development/r4-native, unreleased)
- Read-only native observation route, consent scenarios, observation tests.
- Single deliberate failure: R3 content-manifest mismatch (unfinished
  successor correctly refuses release identity).
