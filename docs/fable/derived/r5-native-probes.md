# Disposable real native expiry and conflict probes

User scope: Finish complete real expiry/fencing and native-conflict probes.

Done means retained real pinned Windows Beads commands, actual five-minute lease expiry without clock/timestamp/TTL overrides, independently reopened results, native compatible merge and same-cell conflict, with negative guarantees reported as REFUTED rather than qualified. Shared databases, installed skills, production activation, original four-trap adoption, and full R5 release remain outside this probe scope.

## Decision and design

Use the pinned released bd.exe for claims, expiry/reclaim, guarded writes and merges. Build a probe-only helper from exact upstream c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c to select real embedded branches. The v1.3.1 CLI has no branch checkout and embedded bd sql refuses, so CLI-only divergent branch construction is unavailable. Fixture-only claims cannot prove native expiry; editing lease timestamps or shortening the TTL would not prove real expiry. A production fencing redesign before observing the gap would expand scope prematurely.

Cortex: source evidence, native commands, and retained readback are distinct evidence families; artifact hashes bind observations. Blueprint: outcome is bounded probes; actors are disposable owner A/B; front door is a qualification CLI; state is isolated .beads; effects are native title changes and branch merges; boundaries require fresh workspace and pinned binary/helper; failures preserve BLOCKED receipts; verification reopens rows/heads and hashes every transcript; handoff retains false generic qualification flags. Weak link is helper CGO/branch feasibility: build and branch roundtrip precede the five-minute wait. GSD/Graphify/Unlazy runtime is not needed for this bounded harness; no successful invocation is claimed.

Scope: .github/scripts/r5_native_probes.py, .github/scripts/r5_native_probe_helper.go, .github/tests/test_r5_native_probes.py, .github/workflows/r5-native-probes.yml, docs/fable intake/requirements/plan/tests/approvals/state/specialists/evidence, this report and docs/STATUS.md. Both installed skill packages and release archives remain byte-identical.

Checklist: establish strict verifier tests RED; implement bounded raw capture and fresh-workspace guard; build exact source helper; test genuine branch ancestry/compatible merge/conflict; wait real lease expiry and test pre/post reclaim and actor ABA; retain failures and successful experiments without promoting refuted guarantees; adversarial review; publish exact reviewed tree and verify exact-head CI.

Risks: native expiry alone may not fence ordinary field edits; assignee/status CAS may not fence ABA. A successful experiment is not a successful guarantee. Merge errors may leave a working set: inspect and report partial effects, never automatically resolve or import accepted proof. Receipt production flags always remain false.
