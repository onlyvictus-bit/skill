# RP1 selected-runtime prototype accepted, 2026-10-31

Verdict: VERIFIED WITH CAVEATS for RP1 scratch prototype only. Parent raw review
and fresh native Fable Sol reviewer both accept the actual normal-account run.
RP2 remains the already-approved next milestone; RP3/full shutdown qualification,
Gate1, release, installation and historical C2 cause proof remain incomplete.

## Bound observation

Normal root: `C:/Users/sakth/Documents/Codex/recursive-launch-rp1-audit-20261029`.
This attempt is consumed. Never rerun its launcher or mutate its outputs.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| run/Receipt.json | 577473 | 20800625e5f4bf72b19c1591b213e94704a48e05e173d93f9f89ff8b4fd76794 |
| Diagnostics.json | 426339 | 344f559d3210de017613fb98ec24c8be43bc8a74e4ea78bd8a8d29f9be28f031 |
| Diagnostics.md | 10797 | be9a2c1e28d34e358f238f333b4b626b05e8ef1fc717a813f88e1b98d7a2f9ff |

Parent freshly rehashed all 639 copied-source files and 116 of 121 bound
evidence files. Five files inside the private expired-gate fixture deny reads
to the agent account. Their complete raw UTF-8 bytes were captured by the normal
account in the sealed Receipt audit_records; parent independently reconstructed
and verified all five lengths and hashes, including failure, contract, ready,
go.tmp and authored root script. This is captured-byte verification, not a fresh
agent reread of those five originals or authenticated-producer proof. No new
permission, copy workaround or user command was required.

## Actual outcomes

- Eleven selected Python 3.12.10 commands, each exit 0; complete capture, no
  timeout, kill path, overflow or capture error. Exact phase order retained.
- Original 17 ownership tests: 17 PASS, zero failures/errors/skips/exclusions.
  unittest log SHA4919845e24ef62e8c266bf86de701208515752e532b1283a340d24ca0713eb02.
- Compatibility matrix: all six original methods PASS; 36 retained raw streams.
  Reviewer compared control/guarded streams. The deliberate exception case adds
  sealed bootstrap frames while retaining authored KeyError, direct-cause
  separator and ValueError. No unreported compatibility deviation was found.
- Exactly two expected negative-control records: E_RP_REQUEST_DIGEST and the
  deliberately expired E_OWNED_BOOTSTRAP_GO_DEADLINE. No unexpected dispatch
  failure. Fresh expired-gate token/identity/ready/go.tmp/script bind correctly;
  final go and authored marker were absent in the normal-account observation.
  Contract deadline2051668.25 lies within the independently calibrated selected
  interval2051665.4824528..2051671.6162488. No historical PID/deadline is accepted
  by the classifier as a future-run constant.
- Smoke actual chain: 7708 -> 48760 -> 10444. Final fresh chain:
  46740 -> 24152 -> 2456. In each, native identities and creation times bind to
  authored markers and pinned handles; all three are in the inner Job. Before:
  active/listed3; after: active/listed0, lifetime total3. All native and launcher
  waits true. Handle/stream/owner release complete, no debt or emergency kill.
- BEFORE/AFTER image and venv identity agree, excluding intentional capture cwd.
  Dependency stream hashes are identical. User-site remains disabled.
- No primary, retention, publication or postcheck error. Fresh normal-account
  postcheck covered original authority inventory, three consumed failure pins,
  helper seals, copied source and then-bound evidence. This is the declared RP1
  preservation scope; full historical-original RP3 BEFORE/AFTER remains separate.

## Recorded time

Top-level measured segments: preflight24.161310s, claim publication0.066788s,
execution34.498796s, original/source/evidence postcheck6.527382s. First segment
start to last segment end is65.265997s; final report-publication time is outside
that interval. Execution includes source copy/profile binding10.971017s.
Original17 capture6.848505s (test body5.615s), matrix6.973645s (body5.740s),
smoke2.121583s, final descendants1.816471s. Dependency checks2.178189s before
and0.690290s after. Nested durations must not be added to their inclusive parent.
Before-stop to after-stop observation spans were6.9953ms and12.8041ms; these are
observation intervals, not isolated shutdown API benchmarks.

## Acceptance and continuation

Fresh native reviewer: SHIP for RP1 scratch prototype acceptance and conditional
RP2 integration. The first review turn was interrupted by workspace credits;
after user CONTINUE the same reviewer resumed and completed the raw assessment.
No selected workload was rerun by the parent or reviewer.

AUTH: existing user approval "Approve RP1-RP3 (Recommended)" and continuation.
INTENT for RP2: integrate the proved recursive native-image launch and pre-work
guard into source-local owned worker startup, retaining public arguments,
identity, error visibility and all original tests. Preserve all old prototypes
and receipts. No new scope approval is needed inside that approved milestone.
RP2 concrete integration mapping, failure-first checks and fresh review precede
RP3. No claim that RP1 alone closes production shutdown or full Gate1.
