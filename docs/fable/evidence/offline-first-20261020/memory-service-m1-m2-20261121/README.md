# AgentMemory M1 and M2 checkpoint

M1 feasibility and M2 isolated deployment passed on Windows on November 21, 2026. The local evidence was reopened and checked against actual REST responses, configuration, native process ledgers, and preservation inventories. Evidence hashes and selected metrics are in [Acceptance.json](Acceptance.json).

- M1 exercised the normal non-admin account, owned process observation, physical directory identity and 22 fixture controls. All 22 passed. These results qualify preparation only.
- M2 used AgentMemory 0.9.33, iii 0.25.1, and pinned state and HTTP workers. The accepted run reused 12,549 verified runtime files. The three authenticated requests returned 200 and an unauthenticated status request returned 401.
- Three owned listeners were on loopback. The supported stop command exited successfully, and native handles confirmed exit for 14 service processes and three stop-command processes. No forced Job termination was recorded. The ports were released.
- The first M2 attempt refused the stop because the isolated launcher PATH omitted Windows PowerShell. The first continuation stopped at a config inspector that looked for the YAML parser in the new data root instead of the reused runtime. The accepted continuation passed both preflight checks, live configuration, authenticated health and shutdown together. Earlier attempts remain retained locally.
- Installed skill files and checked original configuration metadata matched before and after. The empty instance did not create a datastore file during M2.

The next milestone is one separately approved canary write, graceful restart, exact readback and cleanup using the same datastore. Memory-service persistence and installed-skill integration remain unverified. This checkpoint contains selected observations and raw-evidence hashes. Raw local files, credentials and service configuration are outside the published scope.
