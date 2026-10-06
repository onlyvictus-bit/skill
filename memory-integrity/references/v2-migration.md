# v2 migration (memory-integrity)

v1 memory verdicts (HEALTHY/UNVERIFIED/DEGRADED/BLIND), bridge files, and
receipts are historical evidence labeled LEGACY_UNVERIFIED. They cannot
satisfy v2 gates. Re-run the strict v2 checks to earn current verdicts;
recreate bridge evidence across a real tested boundary.

If the companion engine changes incompatibly, the handshake reports
E_SCHEMA_MISMATCH or E_DIGEST_MISMATCH with the expected and observed
values. Update the pin in `scripts/memory_integrity_v2.py` only by
deliberate contract review, never automatically, and re-run the handshake
tests after any change.
