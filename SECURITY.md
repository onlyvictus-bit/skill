# Security policy

Report vulnerabilities privately to the repository owner. Enable GitHub
private vulnerability reporting in the repository settings (required setup;
not verified from this tree), and do not open public issues for unpatched
security defects.

## Scope and boundaries (always true for this project)

- No credentials, API keys, tokens, or private host logs belong in the tree.
  The `.gitignore` excludes caches, databases (`*.db`), and local pilot
  workspaces. Never commit a live `.beads/` database, run ledger, or receipt
  containing secrets.
- The native observer runs a pinned `bd.exe` with shell execution disabled,
  bounded timeouts/output, and exact retained pipe bytes. Native writes stay
  disabled until the qualified adapter lands; read-only observation must never
  activate writes, claims, or merges.
- Unsigned commits and unprotected branches are the current state (see
  CHANGELOG/STATUS). Release tags must be signed once a maintainer key exists;
  until then, verify releases by the SHA-256 checksums in the release manifest,
  not by tag names alone.
