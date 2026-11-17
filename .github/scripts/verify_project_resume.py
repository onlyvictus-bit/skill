"""Project compatibility entry point; reusable logic lives in Memory Integrity."""
import importlib.util
from pathlib import Path

path=Path(__file__).resolve().parents[2]/'memory-integrity/scripts/project_continuity.py'
spec=importlib.util.spec_from_file_location('project_continuity',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
check_basis=module.check_basis
resume=module.resume
readonly_audit=module.readonly_audit
subprocess=module.subprocess

if __name__=='__main__': raise SystemExit(module.main())
