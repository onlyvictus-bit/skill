#!/usr/bin/env python3
"""M6: PDF inventory with the standard library only. No text extraction.

Reports page-count evidence with an explicit confidence level, encryption,
and unreadable regions. A heuristic count is labeled heuristic and can
never support an exactness claim; only a trailer-declared /Count that
agrees with an object scan earns INVENTORY_CHECKED.
"""
import re

PAGE_RE = re.compile(rb"/Type\s*/Page[^s]")
COUNT_RE = re.compile(rb"/Count\s+(\d+)")
ENCRYPT_RE = re.compile(rb"/Encrypt")
XREF_RE = re.compile(rb"startxref\s*(\d+)")


class PdfError(ValueError):
    pass


def inventory_pdf(data):
    """Inventory PDF bytes. Returns counts plus a confidence label."""
    if not isinstance(data, (bytes, bytearray)):
        raise PdfError("E_PDF_TYPE: bytes required")
    if not data.startswith(b"%PDF-"):
        raise PdfError("E_PDF_MAGIC: missing %PDF- header")
    if data.rstrip().endswith(b"%%EOF") is False:
        truncated = True
    else:
        truncated = False
    encrypted = ENCRYPT_RE.search(data) is not None
    counts = [int(m.group(1)) for m in COUNT_RE.finditer(data)]
    scanned = len(PAGE_RE.findall(data))
    xref = XREF_RE.search(data) is not None
    if encrypted:
        return {"pages_best": None, "method": "blocked",
                "confidence": "unknown", "encrypted": True, "truncated": truncated,
                "unreadable": ["encrypted content"]}
    if counts and max(counts) == scanned and scanned > 0:
        confidence, method, pages = "checked", "trailer-agrees-with-scan", max(counts)
    elif counts and max(counts) > 0:
        confidence, method, pages = "heuristic", "trailer-count-only", max(counts)
    elif scanned > 0:
        confidence, method, pages = "heuristic", "object-scan-only", scanned
    else:
        confidence, method, pages = "unknown", "no-evidence", None
    unreadable = []
    if truncated:
        unreadable.append("missing %%EOF: tail may be truncated")
    if not xref:
        unreadable.append("no startxref: cross-reference table absent")
    return {"pages_best": pages, "method": method, "confidence": confidence,
            "encrypted": False, "truncated": truncated, "unreadable": unreadable}


def readiness(inventory):
    if inventory.get("encrypted"):
        return "BLOCKED"
    if inventory.get("truncated") or inventory.get("unreadable"):
        return "PARTIAL"
    if inventory["confidence"] == "checked":
        return "INVENTORY_CHECKED"
    if inventory["confidence"] == "heuristic":
        return "PARTIAL"
    return "UNKNOWN"
