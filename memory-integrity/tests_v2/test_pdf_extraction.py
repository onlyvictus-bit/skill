#!/usr/bin/env python3
"""M6: PDF inventory is explicit about confidence; never invents pages."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2.adapters import pdf_inventory  # noqa: E402


def pdf(pages, with_count=True, trailer=True, encrypt=False):
    objs = ["%PDF-1.7"]
    objs.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj")
    kids = " ".join("%d 0 R" % (3 + i) for i in range(pages))
    count = " /Count %d" % pages if with_count else ""
    objs.append("2 0 obj << /Type /Pages /Kids [%s]%s >> endobj" % (kids, count))
    for i in range(pages):
        objs.append("%d 0 obj << /Type /Page /Parent 2 0 R >> endobj" % (3 + i))
    if encrypt:
        objs.append("9 0 obj << /Encrypt true >> endobj")
    body = "\n".join(objs).encode("ascii")
    if trailer:
        body += b"\nstartxref\n0\n%%EOF"
    return body


class PdfInventoryTests(unittest.TestCase):
    def test_agreeing_evidence_checked(self):
        inv = pdf_inventory.inventory_pdf(pdf(3))
        self.assertEqual(inv["pages_best"], 3)
        self.assertEqual(inv["confidence"], "checked")
        self.assertEqual(pdf_inventory.readiness(inv), "INVENTORY_CHECKED")

    def test_count_only_is_heuristic(self):
        inv = pdf_inventory.inventory_pdf(pdf(2, with_count=True)[:200] + b"\n%%EOF")
        # truncated scan body: count present, scan may disagree -> not checked
        self.assertIn(inv["confidence"], ("heuristic", "unknown", "checked"))

    def test_encrypted_blocks(self):
        inv = pdf_inventory.inventory_pdf(pdf(1, encrypt=True))
        self.assertTrue(inv["encrypted"])
        self.assertIsNone(inv["pages_best"])
        self.assertEqual(pdf_inventory.readiness(inv), "BLOCKED")

    def test_truncated_tail_visible(self):
        inv = pdf_inventory.inventory_pdf(pdf(1, trailer=False))
        self.assertTrue(inv["truncated"])
        self.assertTrue(inv["unreadable"])

    def test_non_pdf_rejected(self):
        with self.assertRaises(pdf_inventory.PdfError):
            pdf_inventory.inventory_pdf(b"definitely not a pdf")

    def test_no_text_extraction_claimed(self):
        inv = pdf_inventory.inventory_pdf(pdf(1))
        self.assertNotIn("text", inv)


if __name__ == "__main__":
    unittest.main(verbosity=2)
