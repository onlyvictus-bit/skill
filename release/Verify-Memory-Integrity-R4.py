"""Verify the formal R4 / m12 Memory Integrity release pair.

Standard-library only. Verifies exact release ZIP hashes, safe archive layout,
internal R4 content manifests, matching m12 engine identity, granular native
capability truth, and all packaged unittest suites. No native Beads mutation,
installation, AI call, or shared-database action is performed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

PACKAGES = ("memory-integrity", "claude-mon")
RELEASE = "2.0.0-m12-r4"
ENGINE_VERSION = "2.0.0-m12"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_members(archive, package):
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
    if len(names) != len(set(names)):
        raise AssertionError("duplicate ZIP member: " + package)
    if sum(name.endswith("/SKILL.md") for name in names) != 1:
        raise AssertionError("invalid SKILL count: " + package)
    for name in names:
        parts = Path(name).parts
        if not name.startswith(package + "/") or ".." in parts or "\\" in name:
            raise AssertionError("unsafe/foreign ZIP member: " + name)
        if "__pycache__" in parts or name.endswith((".pyc", ".pyo")):
            raise AssertionError("cache member: " + name)
    return names


def run_suite(root, suite):
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", suite, "-v"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=360,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8"),
    )
    output = proc.stdout + proc.stderr
    count = re.search(r"Ran (\d+) tests?", output)
    if proc.returncode or count is None:
        print(output)
        raise AssertionError(root.name + "/" + suite + " failed")
    return {"package": root.name, "suite": suite, "tests": int(count.group(1)), "exit_code": 0}


def verify(folder):
    manifest_path = folder / "Memory-Integrity-R4-Release-Manifest.json"
    release = json.loads(manifest_path.read_text(encoding="utf-8"))
    if release.get("release") != RELEASE:
        raise AssertionError("wrong R4 release identity")
    if set(release.get("packages", {})) != set(PACKAGES):
        raise AssertionError("release pair incomplete")
    if release.get("native_shared_claim_qualified") is not True:
        raise AssertionError("shared claim protocol is not qualified")
    if release.get("native_beads_qualified") is not False:
        raise AssertionError("generic native qualification must remain false")
    if release.get("native_merge_qualified") is not False:
        raise AssertionError("native merge qualification must remain false")

    with tempfile.TemporaryDirectory(prefix="mi-r4-check-") as tmp:
        base = Path(tmp)
        for package in PACKAGES:
            info = release["packages"][package]
            archive = folder / info["zip"]
            raw = archive.read_bytes()
            if sha(raw) != info["sha256"]:
                raise AssertionError("ZIP digest mismatch: " + package)
            if len(raw) != info["bytes"]:
                raise AssertionError("ZIP byte count mismatch: " + package)
            names = safe_members(archive, package)
            if len(names) != info["entries"]:
                raise AssertionError("ZIP entry count mismatch: " + package)
            with zipfile.ZipFile(archive) as z:
                z.extractall(base)

            root = base / package
            content_path = root / "tests_v2" / "R4-CONTENT.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            if content.get("release") != RELEASE:
                raise AssertionError("internal R4 content identity mismatch: " + package)
            actual = {
                p.relative_to(root).as_posix(): sha(p.read_bytes())
                for p in root.rglob("*")
                if p.is_file()
                and "__pycache__" not in p.parts
                and p.suffix != ".pyc"
                and p != content_path
            }
            if actual != content["files"]:
                raise AssertionError("content manifest mismatch: " + package)

            caps = json.loads((root / "capabilities-v2.json").read_text(encoding="utf-8"))
            if caps.get("engine_version") != ENGINE_VERSION:
                raise AssertionError("engine version mismatch: " + package)

        mi_caps = json.loads((base / "memory-integrity" / "capabilities-v2.json").read_text(encoding="utf-8"))
        if mi_caps.get("native_shared_claim_protocol_qualified") is not True:
            raise AssertionError("MI shared claim protocol flag missing")
        if mi_caps.get("native_beads_qualified") is not False:
            raise AssertionError("MI generic native flag must remain false")
        if mi_caps.get("generic_native_write_qualified") is not False:
            raise AssertionError("MI generic native write flag must remain false")
        if mi_caps.get("native_merge_qualified") is not False:
            raise AssertionError("MI native merge flag must remain false")

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda pair: run_suite(base / pair[0], pair[1]),
                [(p, s) for p in PACKAGES for s in ("tests", "tests_v2")],
            ))

    out = {
        "ok": True,
        "release": RELEASE,
        "tests": sum(row["tests"] for row in results),
        "suites": results,
        "evidence_class": "NATIVE_VERIFIED",
        "native_shared_claim_protocol_qualified": True,
        "native_beads_qualified": False,
        "native_merge_qualified": False,
        "installed_promoted": False,
    }
    print(json.dumps(out, indent=2))
    print("R4_PORTABLE_VERIFIED")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    verify(args.zip_dir.resolve())
