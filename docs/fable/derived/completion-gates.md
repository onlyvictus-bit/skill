# Gates: Full offline workflow

OWNS: memory-integrity/**, release/**, docs/fable/**

Scope: Derived checks for canonical REQ-15 through REQ-23. Fable retains authority. Run with the explicitly selected KNOWLEDGE_WORKER_PYTHON; host-only skips cannot satisfy G1.

- [x] G1: Actual pinned-runtime extraction, text retrieval, invalidation, tests and admission including adversarial controls
  CHECK: python -B -m unittest discover -s memory-integrity/tests_v2 -p test_knowledge*.py
  EXPECT: /Ran [1-9][0-9]* tests[\s\S]*\nOK(?:\r?\n|$)/
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/workspace/scratch/e3824afcb585/skill-final; path=000535d6a7a1/13 entries; output=Ran 123 tests in 115.820s | OK

- [x] G2: Matching current portable pair and unchanged historical packages pass all declared suites
  CHECK: python -B release/Verify-Knowledge-Bridge.py
  EXPECT: KNOWLEDGE_BRIDGE_PORTABLE_VERIFIED
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/workspace/scratch/e3824afcb585/skill-final; path=000535d6a7a1/13 entries; output=} | KNOWLEDGE_BRIDGE_PORTABLE_VERIFIED
