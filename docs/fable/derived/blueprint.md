# Blueprint: governed bridge v1

## 1. Requirements and ownership

REQ-01..12 and atomized criteria in requirements.json are the canonical matrix. Architect owns isolation/authority, developer owns exact contracts/request binding, tester owns fault evidence, SRE owns persistence/recovery/release, security owns current-permission boundaries, designer owns CLI states. User-visible goal: optionally find linked sources and inspect why a declared proposition was lost while preserving the existing workflow.

Hidden requirements classified: current access and drift required; empty/partial/error/offline states required; single-writer concurrency, resume/audit and portable export required; timestamps/UTF-8 required; rollback required. Pagination/network-service availability/mobile visual layout rejected as inapplicable to this local CLI. Automatic background mutation, second manager and self-qualified semantic truth rejected. Live model services and incremental rebuild are future.

## 2. NFRs and measurements (architect)

| Bound | Target | Check |
|---|---|---|
| Protocol/source bytes | 8 MiB; sources <=1000 | Strict decoder and freeze budget |
| Projection | nodes <=10000, edges <=40000 | Contract/worker rejection |
| Retrieval | seeds 1–100, hops 0–8, visits <=10000, results <=1000 | Bound checks and limit receipts |
| Vector dimension | 1–4096, finite/nonzero, exact model | Vector/model tests |
| Worker | configured <=120 sec; stdout 8 MiB; stderr 64 KiB; no resend | Timeout/output supervision |
| Evidence bytes | independently declared task.max_bytes <=8 MiB | Refuse oversized mandatory scope |
| Persistence | one writer and atomic CURRENT | Interrupted-publication fault |

No service p95/availability/RPS/cost SLO exists for this offline CLI. Benchmark measures initial build, warm source load, worker startup+query and retained bytes. Worst-case 1x budget 10k nodes/40k edges; 10x/100x is rejected, never silently serviced. No scalability claim. File fsync plus atomic replacement does not establish power-loss durability on every filesystem.

## 3. Components and data flow (developer)

Fable task contract -> Memory Integrity source manifests -> permitted projection -> isolated real Semantica vectors/one-hop graph/provenance/SHACL -> reopened evidence pack -> existing claude-mon measured request/context -> accepted CAS/ledger -> execution sidecar -> protected verify/structured audit -> Fable decision. Derived data cannot mutate canonical requirements or approvals.

## 4. Surface state matrix (designer)

| Surface | Empty/loading | Partial/offline | Error/stale | Success |
|---|---|---|---|---|
| status | companion handshake then bounded worker | no worker => DEGRADED/BLOCKED graph | pin/companion/runtime error | actual runtime identity |
| index | absent index permitted, empty sources rejected | retained interrupted build | busy lock/source drift/corruption | immutable generation/current pointer |
| retrieve | no candidates, mandatory units retained | declared nongraph => direct degraded | revoked mandatory scope, stale source, model/budget mismatch | SOURCE_REOPENED; semantic/coverage unverified |
| protected run/verify | new isolated run | unknown accepted delivery stays canonical unresolved | missing/changed pack/task/receipt | exact offline CAS binding |
| audit | empty denominator => null | unobserved/partial stage => limitations | lost/reversed/unsupported/source-mismatched proposition | only declared structured checks passed |

CLI text/JSON supports keyboard/terminal use and UTF-8. Visual contrast, breakpoints and screen-reader-specific graphical widgets are inapplicable; no new visual UI. Structured error codes and null rather than misleading percentage preserve accessibility of state.

## 5. Test matrix (tester)

Unit contracts: duplicates, nonfinite values, path escape, invalid endpoints/unit/types/conditions/time/vector, derivation cycles, mandatory budgets, source hashes and false metadata. Runtime integration: graph+vector multi-hop, permissions/expiry, true premise lineage, actual SHACL, wrong pin, visits, non-axis replay and cancellation. Public e2e: exact request context and response CAS sidecar, stale/revoked/missing receipt, downgrade, changed task/pack, protected audit map and copied map. Existing four suites preserve unknown delivery/history and native guards. Mechanistic benchmark uses three held-out synthetic fixtures x three repeats x four configurations. Optional runtime tests explicitly skip without selected interpreter; this is not runtime readiness.

## 6. Observability/runbook/rollback (SRE)

Receipts expose generation and basis digests, retained source-unit bytes, paths/edge IDs, reached budgets, aggregate exclusions, actual lineage/checksums, SHACL status and observed/unknown audit stages. No fabricated network counts. Treat pin failure, stale basis, protected history error or timeout as blocking events; no automatic retry. Runbook: check identity/current inputs, reconcile stale writer lock with process state, rebuild into new generation, use fresh isolated run for changed basis. Preserve historical results. Roll back with retained paired R4 ZIPs or a Git revert; graph-required v1 history still needs bridge verification. No network service dashboard/automatic alerts or distributed backup scheduler applies; operator backs up protected source/index/run directories.

## 7. Security posture (security)

Trust boundaries: trusted policy/task -> local source, host -> selected dependency worker, persisted generation -> current sources, pack -> measured request, oracle -> semantic gate. Forged metadata, stale/revoked inputs and missing CAS receipts are refused. Source/path/JSON/budget validation is explicit; secrets/provider settings are excluded from worker env. Current access is operator policy, not a hosted auth service. Raw index files contain source text; OS permissions must protect them. Python socket blocking is not an OS sandbox. No HTTP/login/payment/web UI exists, so web OWASP routes are inapplicable. Dependencies are pinned but not hash-authenticated; Semantica MIT license retained by upstream install, no source vendoring.

## 8. Gaps and closing tests

P0 faults found by reviews (empty pass, label/path/premise spoof, audit history/task mismatch, explicit downgrade, rounding drift, optional embedding provenance) were closed with observed regressions. P1 semantic oracle/vector adequacy remains; cheapest close is independent held-out project evaluation. P1 whole-generation rebuild/worker startup cost remains; instrument representative workload before optimizing. P1 OS sandbox/platform power-loss durability requires a separately defined threat/runtime target. Default graph remains off.

## 9. Roadmap/exit state

M0 freeze/decision; M1 real isolated skeleton; M2 structural source-bound projection; M3 local governed retrieval; M4 exact request trace; M5 narrow structured audit; M6 lifecycle failures; M7 fixture comparison and paired portable release. Exit evidence and limitations are in verification.md. Broad semantic understanding, live providers, active install replacement and representative superiority are future, so this release is offline mechanism qualification only.
