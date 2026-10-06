#!/usr/bin/env python3
"""M9: deterministic acceptance corpora. Generated, never stored.

Ground-truth corpus plants checkable facts at start, middle, end, and chunk
boundaries, plus long sentences, Unicode, a distant definition, and an
exception that changes an earlier rule. Scale fixtures are exact byte sizes
of repeated structured lines (mechanical scale only, not semantic proof).
"""
import hashlib

LONG_SENTENCE = ("This deliberately overlong sentence carries the invoice total of "
                 "4821 coins across many filler words so that length handling, "
                 "token estimation, and unit subdivision can be observed " + "and padding. ") * 6
UNICODE_LINE = "Unicodecaf\u00e9 na\u00efve \u4e2d\u6587 \U0001f600 ok"
DEFINITION = "DEFINITION Ledger-7: a settled entry is final and must not be altered."
EXCEPTION = ("EXCEPTION to Ledger-7 (appendix): settlement voids apply within "
             "one day; amount 99 is the void threshold.")


def ground_truth_corpus():
    """Small corpus with known answers and a distant definition/exception pair."""
    lines = [
        "FACT-START fee 42 USD per quarter, never waived.",
        "filler line one about ordinary operations",
        LONG_SENTENCE,
        UNICODE_LINE,
        DEFINITION,
        "filler line two about ordinary operations",
        "FACT-MIDDLE refunds must not exceed 30 days.",
        "filler line three about ordinary operations",
        "FACT-END contact ledger@example.com before noon.",
        EXCEPTION,
    ]
    text = "\n".join(lines) + "\n"
    data = text.encode("utf-8")
    return {"bytes": data, "sha256": hashlib.sha256(data).hexdigest(),
            "facts": {"start": "42", "middle": "30", "negation": "must not",
                      "definition": "Ledger-7", "exception": "99"}}


def scale_fixture(size_bytes):
    """Exact-size mechanical fixture of whole structured lines.

    All lines but possibly the last share one shape; a final padded line
    absorbs any remainder so the total is exact and every line is whole.
    """
    head = "unit %08d | payload abcdefghijklmnopqrstuvwxyz 0123456789 | end\n"
    unit_len = len((head % 0).encode("utf-8"))
    full, rest = divmod(size_bytes, unit_len)
    if full == 0:
        raise ValueError("E_FIXTURE_SIZE: %d smaller than one line" % (size_bytes,))
    lines = [head % i for i in range(full)]
    if rest:
        if rest < 24:
            lines = lines[:-1]
            rest += unit_len
        stem = "unit %08d | pad " % full
        pad_len = rest - len(stem.encode("utf-8")) - 1
        lines.append(stem + "x" * pad_len + "\n")
    data = "".join(lines).encode("utf-8")
    assert len(data) == size_bytes, (len(data), size_bytes)
    assert data.endswith(b"\n") and b"\r" not in data
    return data
