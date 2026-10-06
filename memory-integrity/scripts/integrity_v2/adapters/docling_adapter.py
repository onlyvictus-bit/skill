#!/usr/bin/env python3
"""M6: Docling qualification shell. No auto-install, no silent fallback.

qualify() reports whether a usable Docling is importable with its version
and structured-JSON capability. convert() refuses unless qualified, and its
result always carries extractor identity plus an element inventory the
caller must reconcile. Without Docling, every rich-document route stays
UNSUPPORTED with the exact missing dependency named.
"""
import importlib.util


class DoclingError(Exception):
    pass


def find_spec():
    return importlib.util.find_spec("docling")


def qualify():
    """Return {'available': bool, ...}. Never installs anything."""
    spec = find_spec()
    if spec is None:
        return {"available": False, "missing": ["docling"],
                "verdict": "UNSUPPORTED",
                "reason": "docling package not installed; no auto-install performed"}
    try:
        import docling
        version = getattr(docling, "__version__", "unknown")
    except Exception as exc:
        return {"available": False, "missing": [], "verdict": "UNSUPPORTED",
                "reason": "docling import failed: %s" % (exc,)}
    try:
        from docling.document_converter import DocumentConverter  # noqa: F401
        structured = True
    except Exception:
        structured = False
    return {"available": structured, "version": version,
            "structured_json": structured,
            "verdict": "QUALIFIED" if structured else "UNSUPPORTED",
            "reason": "" if structured else "DocumentConverter unavailable"}


def convert(source_path, *, require_qualified=True):
    """Convert via Docling, or refuse with the exact gap. No fallback."""
    status = qualify()
    if not status["available"]:
        if require_qualified:
            raise DoclingError("E_DOCLING_UNAVAILABLE: %s" % (status["reason"],))
        return {"verdict": "UNSUPPORTED", "missing": status.get("missing", []),
                "elements": [], "diagnostics": {"attempted": False}}
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(str(source_path))
    doc = result.document
    try:
        canonical = doc.save_as_json() if hasattr(doc, "save_as_json") else doc.export_to_dict()
    except Exception as exc:
        raise DoclingError("E_DOCLING_SERIALIZE: %s" % (exc,))
    import json as _json
    payload = canonical if isinstance(canonical, str) else _json.dumps(canonical)
    return {"verdict": "CONVERTED", "version": status["version"],
            "canonical_json": payload,
            "diagnostics": {"status": getattr(result, "status", "unknown")}}
