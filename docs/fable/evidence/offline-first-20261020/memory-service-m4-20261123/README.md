# Memory Integrity M4 and portable-pair qualification

**M4 verdict: PASS for explicit use of the installed Memory Integrity watchdog with the isolated AgentMemory 0.9.33 instance.** The November 23, 2026 Windows run completed all five stages with no runtime or cleanup failures.

- Offline installed-pair checks before and after the test returned the same Claude-Mon 2.0.0-m12 capability envelope and schema digest. The companion remained on its offline profile.
- The installed watchdog made one scoped canary write, matched the ID, content and scope by direct readback, and found it by scoped search. It deleted exactly one item, confirmed HTTP 404 by ID and verified search absence.
- The service used the qualified loopback configuration. Native shutdown evidence accounted for 14 service processes and three stop-command processes with graceful exits and no forced termination. The qualification ports had no listeners after shutdown.
- Full M3 graceful-restart persistence acceptance remains separately documented in the [M3 evidence](../memory-service-m3-20261122/README.md). Automatic Codex recall is unverified. Claude-Mon live dispatch remains disabled.

## Portable pair built from repaired source

The local qualification used exact source commit `d076fefef258d6f03b3b8a0ba33bc9887d757f72`. Two fresh builds reproduced the same bytes, and the archive verifier covered 204 Memory Integrity files and 75 Claude-Mon files after extraction. The extracted pair passed 21 watchdog, 20 companion and 11 Claude-Mon CLI tests. A fresh process recovered all eight relocated v10 records in an isolated project and refused a different skill root containing the same package bytes.

| Local artifact | SHA-256 |
| --- | --- |
| memory-integrity-offline-v1.zip | `2c48e431c122c205ce4a13a9c740d3511218dbcf87ce9fdbbc3fe5d78247ae58` |
| claude-mon-offline-v1.zip | `5c8794b5c332905eb1edf5c9eabe9a096ea0918fd57c6ee62d46b13461fe3383` |
| Offline-First-Release-Manifest.json | `88b388e27ab9d269dffe3c9330ed6f6a5db70ae63960c923943fb74738ce5966` |

The table records the newly built local artifacts. A GitHub reader should verify the same hashes before using any downloadable copy. The older November 15 archives carry different hashes and predate the later repairs. This document contains a scope-limited summary. The raw canary and machine-local recovery receipts remain with the qualification records. An installation and acceptance run under a separate account is pending.
