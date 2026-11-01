# Reusable RP2 / RP3-preparation checkpoint

RP2 source integration is accepted. RP3 input preparation succeeded under the
normal account; the full RP3 selected-runtime and preservation stage is pending.

`Observed-Result.json` records the freshly verified normal output hashes, timing,
eight-root coverage and unresolved counts. Raw Inputs.json, BEFORERequest.json,
private evidence, caches, environments and binaries remain local.

`Archive-Manifest.json` maps eleven byte-exact snapshots to their original
repository paths. The `.snapshot` files are archival evidence, not runnable
helpers at this location. Their paths and existing consumed commands are bound
to the original session. Do not execute these snapshots or retry a consumed
preparation. Reuse the implementation and verified contracts in a separately
reviewed continuation; keep old baselines intact.

The archive preserves RP2 acceptance/baseline, unchanged compatibility assertions
and their wrapper, plus RP3 source recipe, preparation helper, controls and outer
command. Production code and its permanent tests are stored in their normal
repository locations in this checkpoint.

## Git arrangement

The local checkpoint is saved as `checkpoint/rp2-rp3-inputs-20261101`, with parent
`fee69861e1f94c54721e5eb773633f9b1d6f9fd3`. The active development branch/HEAD
and its index remain unchanged so the already-prepared RP3 input guards retain
their meaning. The checkpoint commit is a storage/reuse record; it does not
change the evaluated source basis or qualify the selected runtime. No push is
part of this save.

## Observed normal preparation

- Inputs.json:135906 bytes,
  SHA77769da92ab1fae7375f86afdc651f770476803ec32f5f0dedcea10bd97ee346.
- BEFORERequest.json:2357236 bytes,
  SHA15086f7604605d6793a5d9ff38dbd8395e56a5a6143535e94f28470b864be4bf.
- Diagnostics.json:2996 bytes,
  SHA99a97258a1ea6848c174a3df1e6d041e125f233a2b85e4223fe11d9501171232.
- Source recipe:680 evaluated records;53 expected dependency versions;8 history
  roots. The cleanup-repair root retains1240 unresolved paths for the cooperating
  existing-access reader. Other seven roots have no unresolved paths.
- First recorded start to last end:142.466013 seconds. Segment durations sum to
  140.618951 seconds; approximately1.847062 seconds is between recorded segments.
  Final diagnostic publication is outside this interval. Largest segments are
  cleanup-repair history41.017145s and authority-after40.633846s.
- `selected_runtime_started`, `runtime_command_issued`, `stage_complete`,
  `preservation`, `gate1_complete`, `release_ready` and `installed` remain false.

Next: fresh cooperating BEFORE copies and readback, one new reviewed selected
Python3.12 integrated run, then fresh ORIGINAL AFTER and raw/preservation review.
No package reinstall or security/permission changes are part of this checkpoint.
