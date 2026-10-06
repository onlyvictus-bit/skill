#!/usr/bin/env python3
"""M6: Office parts inventoried independently; macros listed, never run."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2.adapters import ooxml_inventory as ooxml  # noqa: E402

CT = ('<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
      'package/2006/content-types"><Default Extension="xml" ContentType="x"/></Types>')


def make_package(entries):
    tmp = tempfile.NamedTemporaryFile(prefix="ooxml-", suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w") as zf:
        zf.writestr("[Content_Types].xml", CT)
        for name, data in entries.items():
            zf.writestr(name, data)
    return tmp.name


class OoxmlInventoryTests(unittest.TestCase):
    def test_docx_body_headers_comments(self):
        path = make_package({
            "word/document.xml": "<w:document><w:body><w:p><w:r><w:t>hi</w:t></w:r></w:p></w:body></w:document>",
            "word/header1.xml": "<w:hdr/>",
            "word/comments.xml": "<w:comments/>",
        })
        inv = ooxml.inventory_ooxml(path)
        kinds = {p["kind"] for p in inv["parts"]}
        self.assertIn("word-body", kinds)
        self.assertIn("word-header-footer", kinds)
        self.assertIn("word-note", kinds)
        self.assertFalse(inv["macros_present"])

    def test_tracked_changes_visible(self):
        path = make_package({
            "word/document.xml": "<w:document><w:ins author=\"x\"><w:r/></w:ins></w:document>",
        })
        inv = ooxml.inventory_ooxml(path)
        self.assertTrue(any("tracked" in u["reason"] for u in inv["unsupported"]))
        self.assertEqual(ooxml.readiness(inv), "PARTIAL")

    def test_xlsx_sheets_and_empty(self):
        path = make_package({
            "xl/worksheets/sheet1.xml": "<worksheet><sheetData><row><c><v>1</v></c></row></sheetData></worksheet>",
            "xl/worksheets/sheet2.xml": "<worksheet><sheetData/></worksheet>",
        })
        inv = ooxml.inventory_ooxml(path)
        self.assertEqual(len([p for p in inv["parts"] if p["kind"] == "sheet"]), 2)
        self.assertTrue(any("empty sheet" in u["reason"] for u in inv["unsupported"]))

    def test_macros_listed_never_run(self):
        path = make_package({
            "word/document.xml": "<w:document/>",
            "word/vbaProject.bin": "MZ fake binary",
        })
        inv = ooxml.inventory_ooxml(path)
        self.assertTrue(inv["macros_present"])
        self.assertTrue(any("never executed" in u["reason"] for u in inv["unsupported"]))

    def test_non_zip_rejected(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(b"not a zip")
        tmp.close()
        with self.assertRaises(ValueError):
            ooxml.inventory_ooxml(tmp.name)

    def test_missing_content_types_rejected(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.close()
        with zipfile.ZipFile(tmp.name, "w") as zf:
            zf.writestr("word/document.xml", "<w:document/>")
        with self.assertRaises(ValueError):
            ooxml.inventory_ooxml(tmp.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
