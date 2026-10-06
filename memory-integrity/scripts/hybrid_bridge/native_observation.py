"""Bounded readonly Beads v1.3.1 observations, without native activation.

Reads are repeated to detect head and working-data drift. They are not an
atomic multi-command transaction; native writes/fencing remain unqualified.
Export includes every issue type and suppresses unrelated key/value memories.
Owner filtering, row caps, missing relations and unsupported semantics cannot
quietly yield a complete graph. CM acceptance is never inferred from a status.
"""
from datetime import datetime, timezone
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import threading

from . import graph
from .native import NativeContractError

COMMIT = "c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c"
RELEASE = "beads-v1.3.1:" + COMMIT
JSON_MIGRATION_NOTE = ("NOTE: bd --json output format will change in v2.0. "
    "Set BD_JSON_ENVELOPE=1 to opt in early. See docs/reference/json-schema.md for migration details.")
READ_COMMANDS = {
    "version": ("version",),
    "info": ("info",),
    "head": ("vc", "status"),
    "export": ("export", "--all", "--no-memories"),
}
MAX_OUTPUT_BYTES = 8 * 1024 * 1024
TIMEOUT_SECONDS = 15
RELATIONS = {"blocks":"hard", "related":"informational", "tracks":"informational",
             "discovered-from":"informational", "caused-by":"informational",
             "validates":"informational", "supersedes":"informational"}


def _fail(code, message=""):
    raise NativeContractError(code + (": " + message if message else ""))


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _ordinary(path, directory=False):
    path = Path(path)
    if not path.is_absolute():
        _fail("E_NATIVE_ABSOLUTE_PATH", str(path))
    for part in (path, *path.parents):
        attrs = part.lstat()
        if part.is_symlink() or getattr(attrs,"st_file_attributes",0) & getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",0):
            _fail("E_NATIVE_LINK_PATH", str(part))
    if directory and not path.is_dir() or not directory and not path.is_file():
        _fail("E_NATIVE_PATH_TYPE", str(path))
    return path.resolve()


def _strict_json(raw):
    def pairs(items):
        out = {}
        for key,value in items:
            if key in out:
                _fail("E_NATIVE_DUPLICATE_JSON_KEY", key)
            out[key] = value
        return out
    def constant(value):
        _fail("E_NATIVE_NONFINITE_JSON", value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def _selection(selection):
    selection.validate()
    if selection.expected_version != "1.3.1" or selection.release_ref != RELEASE:
        _fail("E_NATIVE_RELEASE", "only the observed v1.3.1 contract is implemented")
    for key in ("expected_project_id","expected_database_name","expected_prefix"):
        value = getattr(selection,key)
        if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9_.-]+",value):
            _fail("E_NATIVE_SELECTION_ID", key)
    exe = _ordinary(selection.executable)
    root = _ordinary(selection.database,directory=True)
    beads = _ordinary(root / ".beads",directory=True)
    metadata_path = _ordinary(beads / "metadata.json")
    database_path = _ordinary(beads / "embeddeddolt",directory=True)
    _ordinary(database_path / selection.expected_database_name / ".dolt",directory=True)
    if _sha(exe.read_bytes()) != selection.executable_sha256.lower():
        _fail("E_NATIVE_EXE_HASH", "selected executable bytes changed")
    metadata_raw = metadata_path.read_bytes()
    metadata = _strict_json(metadata_raw)
    expected = {"database":"dolt", "backend":"dolt", "dolt_mode":"embedded",
                "dolt_database":selection.expected_database_name, "project_id":selection.expected_project_id}
    if not isinstance(metadata,dict) or any(metadata.get(k)!=v for k,v in expected.items()):
        _fail("E_NATIVE_METADATA", "selected embedded project/database does not match")
    return exe,root,beads,database_path,metadata_raw


def _decode(raw):
    if not isinstance(raw,bytes):
        _fail("E_NATIVE_CAPTURE", "byte capture required")
    if len(raw)>MAX_OUTPUT_BYTES:
        _fail("E_NATIVE_OUTPUT_LIMIT", "captured output exceeds bounded observation size")
    return raw.decode("utf-8",errors="strict")


def _retain_pipe(record,name,raw):
    """Retain exact captured bytes; the display text is only a convenience."""
    if not isinstance(raw,bytes):
        _fail("E_NATIVE_CAPTURE", "byte capture required for " + name)
    record[name] = raw.decode("utf-8",errors="replace")
    record[name+"_base64"] = base64.b64encode(raw).decode("ascii")
    record[name+"_sha256"] = _sha(raw)
    record[name+"_captured_bytes"] = len(raw)


def _capture_process(args, *, cwd, env, timeout, shell=False):
    """Capture both pipes with a byte limit while the child is running.

    Killing here targets only the process we created. Reader completion and
    process exit are checked separately; a surviving pipe/child refuses proof.
    """
    if shell is not False:
        _fail("E_NATIVE_SHELL", "native commands must use an argument array")
    process = subprocess.Popen(args,cwd=cwd,env=env,shell=False,stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    data = {"stdout":bytearray(),"stderr":bytearray()}
    complete = {"stdout":False,"stderr":False}
    errors = []
    overflow = threading.Event()
    def stop():
        try:
            if process.poll() is None:
                process.kill()
        except OSError as exc:
            errors.append("termination: " + str(exc))
    def read(pipe,name):
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    complete[name] = True
                    break
                remaining = MAX_OUTPUT_BYTES-len(data[name])
                data[name].extend(chunk[:remaining])
                if len(chunk)>remaining:
                    overflow.set()
                    stop()
                    break
        except OSError as exc:
            errors.append(name + ": " + str(exc))
        finally:
            pipe.close()
    readers = [threading.Thread(target=read,args=(pipe,name),daemon=True)
               for pipe,name in ((process.stdout,"stdout"),(process.stderr,"stderr"))]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        stop()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            errors.append("termination: child did not exit after kill")
    for reader in readers:
        reader.join(timeout=5)
    return {"exit_code":process.poll(),"stdout":bytes(data["stdout"]),"stderr":bytes(data["stderr"]),
            "capture_complete":all(complete.values()) and not any(r.is_alive() for r in readers),
            "timed_out":timed_out,"output_limit_exceeded":overflow.is_set(),
            "capture_errors":errors,"process_id":process.pid}


def _command(exe,root,beads,kind,observations,expected_digest):
    if kind not in READ_COMMANDS:
        _fail("E_NATIVE_READ_COMMAND", kind)
    if _sha(_ordinary(exe).read_bytes())!=expected_digest.lower():
        _fail("E_NATIVE_EXE_HASH", "selected executable changed before command")
    args = [str(exe),"--sandbox","--actor","memory-integrity-pilot","--json","--readonly",
            *READ_COMMANDS[kind]]
    env = {k:v for k,v in os.environ.items()
           if not k.upper().startswith(("BEADS_","BD_","DOLT_"))}
    env.update(BEADS_DIR=str(beads),BD_DISABLE_METRICS="1",BD_JSON_ENVELOPE="0")
    record = {"kind":kind,"arguments":args,"working_directory":str(root),
              "started_at_utc":datetime.now(timezone.utc).isoformat(),
              "timed_out":False,"capture_complete":False,"exit_code":None,
              "stdout":None,"stderr":None,"timeout_seconds":TIMEOUT_SECONDS}
    observations.append(record)
    try:
        completed = _capture_process(args,cwd=root,env=env,shell=False,timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        record["timed_out"] = True
        _retain_pipe(record,"stdout",exc.stdout or b"")
        _retain_pipe(record,"stderr",exc.stderr or b"")
        _fail("E_NATIVE_TIMEOUT", kind)
    finally:
        record["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    # Save complete raw data before interpreting or rejecting it.
    record.update(exit_code=completed["exit_code"],
                  capture_complete=completed["capture_complete"],timed_out=completed["timed_out"],
                  output_limit_exceeded=completed["output_limit_exceeded"],
                  capture_errors=completed["capture_errors"],process_id=completed["process_id"])
    _retain_pipe(record,"stdout",completed["stdout"])
    _retain_pipe(record,"stderr",completed["stderr"])
    if completed["output_limit_exceeded"]:
        _fail("E_NATIVE_OUTPUT_LIMIT", kind)
    if completed["timed_out"]:
        _fail("E_NATIVE_TIMEOUT", kind)
    if completed["capture_complete"] is not True or completed["capture_errors"]:
        _fail("E_NATIVE_CAPTURE", "incomplete pipe capture or process termination")
    stdout,stderr = _decode(completed["stdout"]),_decode(completed["stderr"])
    unexpected = [line for line in stderr.splitlines() if line.strip() and line.strip()!=JSON_MIGRATION_NOTE]
    if unexpected:
        _fail("E_NATIVE_DIAGNOSTIC", " | ".join(unexpected))
    if type(completed["exit_code"]) is not int or completed["exit_code"] != 0:
        _fail("E_NATIVE_EXIT", "%s exited %s: %s" % (kind,completed["exit_code"],stdout))
    return stdout


def _object(raw,kind):
    value = _strict_json(raw)
    if not isinstance(value,dict) or type(value.get("schema_version")) is not int or value["schema_version"]!=1 or "error" in value:
        _fail("E_NATIVE_JSON_SCHEMA", kind)
    return value


def _info(value,database_path,prefix):
    if not isinstance(value.get("database_path"),str) or os.path.normcase(os.path.abspath(value["database_path"]))!=os.path.normcase(str(database_path)):
        _fail("E_NATIVE_DATABASE_PATH", "readback selected another database")
    if value.get("mode")!="direct" or type(value.get("issue_count")) is not int or value["issue_count"]<0:
        _fail("E_NATIVE_INFO_SCHEMA", "direct mode and nonnegative integer issue count required")
    if not isinstance(value.get("config"),dict) or value["config"].get("issue_prefix")!=prefix:
        _fail("E_NATIVE_PREFIX", "readback prefix differs from selected project")
    return value["issue_count"]


def _head(value):
    for key in ("branch","commit"):
        if not isinstance(value.get(key),str) or not value[key].strip():
            _fail("E_NATIVE_HEAD_SCHEMA", key)
    return {"branch":value["branch"],"head":value["commit"]}


def _claim(issue,now):
    actor = issue.get("assignee")
    lease = issue.get("lease_expires_at")
    result = {"actor":actor,"lease_expires_at":lease,"effective":False,
              "reason":"UNCLAIMED", "fence_qualified":False}
    if issue["status"]!="in_progress":
        return result
    result["reason"] = "UNKNOWN_ACTOR"
    if not isinstance(actor,str) or not actor.strip() or actor.lower()=="unknown":
        return result
    result["reason"] = "MISSING_OR_INVALID_LEASE"
    if not isinstance(lease,str):
        return result
    try:
        expiry = datetime.fromisoformat(lease.replace("Z","+00:00"))
        if expiry.utcoffset() is None:
            return result
    except ValueError:
        return result
    result["reason"] = "EXPIRED" if expiry<=now else "LEASE_OBSERVED_FENCE_UNQUALIFIED"
    # A timestamp/assignee is not a native fencing token. M7 must qualify the
    # supported single-writer protocol before this can become effective.
    return result


def _export(raw,expected_count,project,prefix):
    issues,edges = {},[]
    for line in raw.splitlines():
        if not line.strip():
            continue
        issue = _strict_json(line)
        if not isinstance(issue,dict) or issue.get("_type")!="issue":
            _fail("E_NATIVE_EXPORT_RECORD", "only selected task issue records are supported")
        ident = issue.get("id")
        if not isinstance(ident,str) or not ident.strip() or ident in issues:
            _fail("E_NATIVE_EXPORT_ID", "missing or duplicate issue identity")
        # Match the selected known prefix using v1.3.1's known-prefix rule,
        # including multi-hyphen prefixes and dotted child task suffixes.
        if not ident.startswith(prefix+"-") or not ident[len(prefix)+1:].strip():
            _fail("E_NATIVE_FOREIGN_PREFIX", ident)
        if not isinstance(issue.get("status"),str) or not issue["status"].strip():
            _fail("E_NATIVE_EXPORT_STATUS", ident)
        dependencies = issue.get("dependencies",[])
        if not isinstance(dependencies,list) or type(issue.get("dependency_count")) is not int or issue["dependency_count"]!=len(dependencies):
            _fail("E_NATIVE_EXPORT_DEPENDENCIES", "missing/truncated relations for " + ident)
        for dep in dependencies:
            if not isinstance(dep,dict) or dep.get("issue_id")!=ident or dep.get("type") not in RELATIONS:
                _fail("E_NATIVE_RELATION", "unsupported or foreign relation for " + ident)
            edges.append({"from":dep.get("depends_on_id"),"to":ident,"relation":RELATIONS[dep["type"]]})
        issues[ident] = issue
    if len(issues)!=expected_count:
        _fail("E_NATIVE_EXPORT_COUNT", "exported %s, observed %s; filters/caps/missing records refuse completeness" % (len(issues),expected_count))
    if not issues:
        _fail("E_NATIVE_EXPORT_EMPTY", "an empty project does not qualify a task graph")
    # Reuse structural policy without passing native data through a TEST_ONLY
    # fixture or the offline-only evidence-class activation check.
    tasks = graph._task_ids(sorted(issues),project)
    normalized = graph._normalise_edges(edges,tasks,project)
    graph._reject_hard_cycles(tasks,normalized)
    return issues,list(normalized)


def observe(selection):
    observations = []
    out = {"schema_version":1,"ok":False,"overall":"BLOCKED_NATIVE_OBSERVATION",
           "active":False,"native_beads_qualified":False,"database_write_performed":False,
           "inference_sent":False,"evidence_class":"NATIVE_OBSERVED_UNQUALIFIED",
           "observations":observations,"blockers":[]}
    try:
        exe,root,beads,db_path,metadata_raw = _selection(selection)
        def command(kind):
            return _command(exe,root,beads,kind,observations,selection.executable_sha256)
        version = _object(command("version"),"version")
        if version.get("version")!=selection.expected_version or version.get("commit")!=COMMIT:
            _fail("E_NATIVE_VERSION", "observed build differs from the pinned contract")
        info = _object(command("info"),"info")
        count = _info(info,db_path,selection.expected_prefix)
        before = _head(_object(command("head"),"head"))
        first = command("export")
        issues,edges = _export(first,count,selection.expected_project_id,selection.expected_prefix)
        second = command("export")
        later_issues,later_edges = _export(second,count,selection.expected_project_id,selection.expected_prefix)
        after = _head(_object(command("head"),"head"))
        later_info = _object(command("info"),"info")
        _info(later_info,db_path,selection.expected_prefix)
        if before!=after or info!=later_info or _canonical(issues)!=_canonical(later_issues) or edges!=later_edges:
            _fail("E_NATIVE_CHANGED_DURING_READ", "head, info or working issue data changed; reobserve")
        _exe,_root,_beads,_db,current_metadata = _selection(selection)
        if current_metadata!=metadata_raw:
            _fail("E_NATIVE_METADATA_CHANGED", "project selection changed during read")
        now = datetime.now(timezone.utc)
        snapshot = {"schema_version":1,"database":str(db_path),"project_id":selection.expected_project_id,
            **after,"tasks":sorted(issues),"edges":edges,"issues":issues,
            "claims":{ident:_claim(issue,now) for ident,issue in issues.items()},
            "observed_at_utc":now.isoformat(),"working_data_digest":_sha(_canonical(issues)),
            "metadata_digest":_sha(metadata_raw),"complete_read":True,
            "complete_read_scope":"issues and exported dependencies in selected embedded project",
            "atomic_read":False,"evidence_class":"NATIVE_OBSERVED_UNQUALIFIED",
            "native":True,"native_beads_qualified":False}
        snapshot["snapshot_digest"] = _sha(_canonical(snapshot))
        out.update(ok=True,overall="NATIVE_SNAPSHOT_OBSERVED_UNQUALIFIED",snapshot=snapshot)
    except Exception as exc:
        out["blockers"].append(type(exc).__name__ + ": " + str(exc))
    return out
