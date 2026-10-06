#!/usr/bin/env python3
"""M6: Office inventory with the standard library only (zipfile + XML).

Reads the OOXML package structure independently of any convenience
extractor so unsupported headers, footers, comments, tracked changes,
hidden slides/sheets, notes, text boxes, and embedded objects stay visible.
Never executes macros; macro parts are reported, never run. Text extraction
is explicitly NOT performed here — this module inventories containers.
"""
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET

WORD_TEXT = "word/document.xml"
WORD_NOTES = ("word/comments.xml", "word/endnotes.xml", "word/footnotes.xml")
WORD_HEADERS = re.compile(r"^word/(header\d*|footer\d*)\.xml$")
SLIDE_RE = re.compile(r"^ppt/slides/slide\d+\.xml$")
SHEET_RE = re.compile(r"^xl/worksheets/sheet\d+\.xml$")
MACRO_PARTS = ("word/vbaProject.bin", "xl/vbaProject.bin", "ppt/vbaProject.bin")
TRACKED_RE = re.compile(r"w:(ins|del|moveFrom|moveTo)")


def _read(zf, name):
    try:
        return zf.read(name)
    except KeyError:
        return None


def inventory_ooxml(path):
    """Return the package inventory. Raises on non-zip/unreadable input."""
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise ValueError("E_OOXML_ZIP: not an OOXML package: %s" % (exc,))
    with zf:
        names = zf.namelist()
        content_types = _read(zf, "[Content_Types].xml")
        if content_types is None:
            raise ValueError("E_OOXML_CONTENT_TYPES: missing [Content_Types].xml")
        parts, unsupported = [], []
        doc = _read(zf, WORD_TEXT)
        if doc is not None:
            parts.append({"part": WORD_TEXT, "kind": "word-body"})
            for note in WORD_NOTES:
                if _read(zf, note) is not None:
                    parts.append({"part": note, "kind": "word-note"})
            for name in names:
                if WORD_HEADERS.match(name):
                    parts.append({"part": name, "kind": "word-header-footer"})
            if TRACKED_RE.search(doc.decode("utf-8", errors="replace")):
                unsupported.append({"part": WORD_TEXT,
                                    "reason": "tracked changes present; review required"})
        slides = sorted(n for n in names if SLIDE_RE.match(n))
        for name in slides:
            parts.append({"part": name, "kind": "slide"})
        for extra in ("ppt/notesSlides",):
            if any(n.startswith(extra) for n in names):
                parts.append({"part": extra, "kind": "speaker-notes"})
        sheets = sorted(n for n in names if SHEET_RE.match(n))
        for name in sheets:
            parts.append({"part": name, "kind": "sheet"})
            data = _read(zf, name) or b""
            text = data.decode("utf-8", errors="replace")
            if "<sheetData/>" in text or "<sheetData />" in text:
                unsupported.append({"part": name, "reason": "empty sheet data"})
        for name in names:
            if name in MACRO_PARTS or name.endswith(".bin") and "vba" in name.lower():
                unsupported.append({"part": name,
                                    "reason": "macro/active content: listed, never executed"})
            if "/embeddings/" in name or name.startswith("embeddings/"):
                unsupported.append({"part": name, "reason": "embedded object: listed, not parsed"})
        hidden = [n for n in names if "/hidden" in n.lower()]
        for name in hidden:
            unsupported.append({"part": name, "reason": "hidden-marked part"})
        workbook = _read(zf, "xl/workbook.xml")
        if workbook is not None:
            try:
                tree = ET.fromstring(workbook)
            except ET.ParseError:
                unsupported.append({"part": "xl/workbook.xml",
                                    "reason": "workbook XML malformed; review required"})
            else:
                for sheet in tree.iter():
                    if sheet.tag.rsplit("}", 1)[-1] != "sheet":
                        continue
                    state = sheet.attrib.get("state", "")
                    if state.lower() in ("hidden", "veryhidden"):
                        name = sheet.attrib.get("name")
                        unsupported.append({"part": "xl/workbook.xml",
                                            "reason": "hidden sheet%s; review required"
                                            % (" %r" % name if name else "")})
        return {"parts": parts, "unsupported": unsupported,
                "part_count": len(names),
                "macros_present": any(u["reason"].startswith("macro") for u in unsupported)}


def readiness(inventory):
    if inventory["unsupported"]:
        return "PARTIAL"
    if not inventory["parts"]:
        return "UNKNOWN"
    return "INVENTORY_CHECKED"
