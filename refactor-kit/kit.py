#!/usr/bin/env python3
"""
Refactoring starter kit for Apache Commons CLI 1.9.0 (SWE 539, Homework 2).

Every LLM goes through the same mechanical steps, all done by this script:

  python kit.py check                                  # tools present?
  python kit.py show W01                               # print a smell from the review sheet
  python kit.py start  --smell W01 --llm "ChatGPT" --model "GPT-5.1"   [--mode chat] [--base REF] [--force]
  python kit.py test   --llm "ChatGPT" [--only HelpFormatterTest]      # run tests in the workspace
  python kit.py apply  --smell W01 --llm "ChatGPT" [--response FILE]   # chat mode: write files from a reply
  python kit.py finish --smell W01 --llm "ChatGPT"                     # test, compare, save, log
  python kit.py metrics --smell W01 --llm "ChatGPT"  [--all]           # CK size/cohesion/coupling -> Metrics sheet
  python kit.py log                                    # rebuild Refactoring_Log.xlsx from runs/
  python kit.py status                                 # list runs

Requirements: Python 3.8+, openpyxl, git, a JDK (javac + javap), Maven.
"""
import argparse
import bisect
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

KIT = Path(__file__).resolve().parent
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CFG = json.loads((KIT / "config.json").read_text(encoding="utf-8"))
SRC_ROOT = CFG["source_root"].strip("/")
EXCEL_CELL_LIMIT = 32000


# ======================================================================================
# small helpers
# ======================================================================================
def die(msg):
    print("\nERROR: " + msg)
    sys.exit(1)


def warn(msg):
    print("WARNING: " + msg)


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s or "llm"


def now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def run(cmd, cwd=None, timeout=None, check=False):
    exe = shutil.which(cmd[0]) or cmd[0]
    full = [exe] + list(cmd[1:])
    if os.name == "nt" and exe.lower().endswith((".cmd", ".bat")):
        full = ["cmd", "/c"] + full
    try:
        p = subprocess.run(full, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except FileNotFoundError:
        die(f"command not found: {cmd[0]}  (run `python kit.py check`)")
    except subprocess.TimeoutExpired:
        die(f"command timed out after {timeout}s: {' '.join(cmd)}")
    if check and p.returncode != 0:
        die(f"command failed ({p.returncode}): {' '.join(cmd)}\n{(p.stdout or '')[-3000:]}")
    return p


def git(ws, *args, check=True):
    return run(["git", *args], cwd=ws, check=check)


def read(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")


def write(p, text):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def rel(p):
    try:
        return Path(p).resolve().relative_to(KIT).as_posix()
    except ValueError:
        return str(p)


def ws_dir(llm):
    return KIT / "workspace" / slug(llm) / "commons-cli"


def run_dir(llm, smell):
    return KIT / "runs" / slug(llm) / smell.upper()


def load_run(llm, smell):
    rd = run_dir(llm, smell)
    if not (rd / "run.json").exists():
        die(f"no run found at {rel(rd)} - start it first with `python kit.py start --smell {smell} --llm \"{llm}\" ...`")
    return rd, json.loads(read(rd / "run.json"))


def save_run(rd, meta):
    write(rd / "run.json", json.dumps(meta, indent=2))


# ======================================================================================
# smells (review sheet + targets)
# ======================================================================================
def read_smells():
    try:
        from openpyxl import load_workbook
    except ImportError:
        die("openpyxl is missing: pip install openpyxl")
    path = KIT / CFG["smells_workbook"]
    if not path.exists():
        die(f"smells workbook not found: {rel(path)} (see config.json 'smells_workbook')")
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb["Code Smells"] if "Code Smells" in wb.sheetnames else wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    try:
        h = next(i for i, r in enumerate(rows) if r and r[0] is not None and str(r[0]).strip() == "ID")
    except StopIteration:
        die("could not find the header row (a cell 'ID' in column A) in the smells workbook")
    hdr = [str(x).strip() if x is not None else "" for x in rows[h]]
    smells = {}
    for r in rows[h + 1:]:
        if not r or r[0] is None or not str(r[0]).strip():
            continue
        d = {hdr[i]: ("" if i >= len(r) or r[i] is None else str(r[i]).strip()) for i in range(len(hdr)) if hdr[i]}
        smells[str(r[0]).strip().upper()] = d
    wb.close()
    return smells


def col(d, *names):
    for n in names:
        for k, v in d.items():
            if k.lower().startswith(n.lower()):
                return v
    return ""


def load_targets():
    p = KIT / CFG["targets_file"]
    return json.loads(read(p)) if p.exists() else {}


def get_smell(smell_id):
    smells = read_smells()
    sid = smell_id.strip().upper()
    if sid not in smells:
        die(f"smell {sid} not in the review sheet. Known IDs: {', '.join(smells)}")
    s = smells[sid]
    t = load_targets().get(sid, {})
    yours = col(s, "Your refactoring approach")
    claude = col(s, "Suggested refactoring")
    how = col(s, "How to apply")
    info = {
        "id": sid,
        "type": col(s, "Smell type"),
        "smell": col(s, "Code smell"),
        "classes": col(s, "Class"),
        "member": col(s, "Method"),
        "lines": col(s, "Lines"),
        "evidence": col(s, "Evidence"),
        "suggested": claude,
        "how": how,
        "effect": col(s, "Expected effect"),
        "risk": col(s, "Behaviour", "Risk"),
        "priority": col(s, "Priority"),
        "decision": col(s, "Decision"),
        "your_approach": yours,
        "reviewer_notes": col(s, "Reviewer notes"),
        "targets": t.get("targets", {}),
        "tests": t.get("tests", []),
    }
    if yours:
        info["technique"] = yours
        info["technique_source"] = "reviewer (column 'Your refactoring approach')"
        info["technique_how"] = yours + ("\n\nReference outline from the sheet: " + how if how else "")
    else:
        info["technique"] = claude
        info["technique_source"] = "review sheet suggestion (column 'Suggested refactoring')"
        info["technique_how"] = how
    return info


# ======================================================================================
# Java member splitter (no external parser; good enough for diffing members)
# ======================================================================================
TYPE_RE = re.compile(r"\b(?:class|interface|enum|record)\s+([A-Za-z_$][\w$]*)|@interface\s+([A-Za-z_$][\w$]*)")


def skip_literal(s, i):
    c = s[i]
    nx = s[i + 1] if i + 1 < len(s) else ""
    if c == "/" and nx == "/":
        j = s.find("\n", i)
        return len(s) if j < 0 else j
    if c == "/" and nx == "*":
        j = s.find("*/", i + 2)
        return len(s) if j < 0 else j + 2
    if c == '"':
        if s.startswith('"""', i):
            j = s.find('"""', i + 3)
            return len(s) if j < 0 else j + 3
        j = i + 1
        while j < len(s):
            if s[j] == "\\":
                j += 2
                continue
            if s[j] in '"\n':
                return j + 1
            j += 1
        return j
    if c == "'":
        j = i + 1
        while j < len(s):
            if s[j] == "\\":
                j += 2
                continue
            if s[j] in "'\n":
                return j + 1
            j += 1
        return j
    return None


def match_brace(s, i):
    depth, j = 0, i
    while j < len(s):
        k = skip_literal(s, j)
        if k is not None:
            j = k
            continue
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise ValueError("unbalanced braces")


def code_only(text):
    """Blank out comments and literal contents, keeping every character position (and newlines) unchanged."""
    out, j = [], 0
    while j < len(text):
        k = skip_literal(text, j)
        if k is not None:
            chunk = text[j:k]
            if text[j] in "\"'":
                q = text[j]
                inner = "".join("\n" if ch == "\n" else " " for ch in chunk[1:-1]) if len(chunk) >= 2 else ""
                out.append(q + inner + (q if len(chunk) >= 2 else ""))
            else:
                out.append("".join("\n" if ch == "\n" else " " for ch in chunk))
            j = k
            continue
        out.append(text[j])
        j += 1
    return "".join(out)


def strip_annotations(code):
    res, j = [], 0
    while j < len(code):
        if code[j] == "@" and not code.startswith("@interface", j):
            m = re.match(r"@[\w.$]+\s*", code[j:])
            j += m.end() if m else 1
            if j < len(code) and code[j] == "(":
                d = 0
                while j < len(code):
                    if code[j] == "(":
                        d += 1
                    elif code[j] == ")":
                        d -= 1
                        if d == 0:
                            j += 1
                            break
                    j += 1
            continue
        res.append(code[j])
        j += 1
    return "".join(res)


def drop_generics(code):
    out, d = [], 0
    for ch in code:
        if ch == "<":
            d += 1
        elif ch == ">" and d:
            d -= 1
        elif d == 0:
            out.append(ch)
    return "".join(out)


def param_types(params):
    parts, cur, d = [], "", 0
    for ch in params:
        if ch in "<([":
            d += 1
        elif ch in ">)]":
            d -= 1
        if ch == "," and d == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    types = []
    for p in parts:
        p = re.sub(r"\bfinal\b", "", strip_annotations(p)).strip()
        m = re.match(r"(.*?)([A-Za-z_$][\w$]*)\s*((?:\[\s*\])*)\s*$", p, re.S)
        t = (m.group(1) + (m.group(3) or "")) if m else p
        types.append(re.sub(r"\s+", "", t))
    return types


def parse_java(src):
    """Return the members of a Java file: imports block, type headers, fields, methods, constructors, initializers."""
    starts = [0] + [m.end() for m in re.finditer("\n", src)]

    def ln(pos):
        return bisect.bisect_right(starts, max(0, pos))

    members = []

    def add(kind, owner, a, b, **extra):
        while a < b and src[a].isspace():
            a += 1
        ls = src.rfind("\n", 0, a) + 1
        if src[ls:a].strip() == "":
            a = ls
        if a >= b:
            return
        m = {"kind": kind, "owner": owner, "start": ln(a), "end": ln(b - 1), "text": src[a:b]}
        m.update(extra)
        members.append(m)

    # top-level type
    i = 0
    while i < len(src):
        k = skip_literal(src, i)
        if k is not None:
            i = k
            continue
        if src[i] == "{":
            break
        i += 1
    if i >= len(src):
        raise ValueError("no type body found")
    pre = code_only(src[:i])
    last_semi = pre.rfind(";")
    pre_end = last_semi + 1 if last_semi >= 0 else 0
    add("imports", "", 0, pre_end, key="(package & imports)", name="(package & imports)")
    m = TYPE_RE.search(strip_annotations(code_only(src[pre_end:i])))
    if not m:
        raise ValueError("no type declaration found")
    top = m.group(1) or m.group(2)
    add("type", "", pre_end, i + 1, key=f"{top} (declaration)", name=top)
    _parse_body(src, i + 1, top, add)

    # unique keys
    seen = {}
    for mem in members:
        k = mem["key"]
        if k in seen:
            seen[k] += 1
            mem["key"] = f"{k} #{seen[k]}"
        else:
            seen[k] = 1
    return members


def _parse_body(src, i, owner, add):
    stmt, pd, has_eq, n, init_no = i, 0, False, len(src), 0
    simple = owner.split(".")[-1]
    while i < n:
        k = skip_literal(src, i)
        if k is not None:
            i = k
            continue
        c = src[i]
        if c == "(":
            pd += 1
        elif c == ")":
            pd -= 1
        elif pd == 0:
            if c == "=" and src[i + 1:i + 2] != "=" and (i == 0 or src[i - 1] not in "=!<>"):
                has_eq = True
            elif c == ";":
                text = src[stmt:i + 1]
                code = strip_annotations(code_only(text)).strip()
                if code and code != ";":
                    before_eq = code.split("=")[0]
                    if "(" in before_eq:
                        nm, types = _method_sig(code)
                        add("method", owner, stmt, i + 1, key=f"{owner}.{nm}({','.join(types)})", name=nm, params=types)
                    else:
                        names = [re.findall(r"[A-Za-z_$][\w$]*", p.strip())[-1:] for p in drop_generics(before_eq.rstrip(";")).split(",")]
                        names = [x[0] for x in names if x]
                        add("field", owner, stmt, i + 1, key=f"{owner}#{','.join(names)}", name=",".join(names), names=names)
                stmt, has_eq = i + 1, False
            elif c == "{":
                if has_eq:
                    i = match_brace(src, i)
                    continue
                hdr = strip_annotations(code_only(src[stmt:i]))
                tm = TYPE_RE.search(hdr)
                if tm:
                    name = tm.group(1) or tm.group(2)
                    q = f"{owner}.{name}"
                    add("type", owner, stmt, i + 1, key=f"{q} (declaration)", name=name)
                    i = _parse_body(src, i + 1, q, add)
                    stmt, has_eq = i, False
                    continue
                e = match_brace(src, i)
                if "(" in hdr:
                    nm, types = _method_sig(hdr)
                    kind = "constructor" if nm == simple else "method"
                    add(kind, owner, stmt, e, key=f"{owner}.{nm}({','.join(types)})", name=nm, params=types)
                else:
                    init_no += 1
                    add("initializer", owner, stmt, e, key=f"{owner} (initializer {init_no})", name="initializer")
                i, stmt, has_eq = e, e, False
                continue
            elif c == "}":
                return i + 1
        i += 1
    return i


def _method_sig(code):
    p = code.find("(")
    name = re.findall(r"[A-Za-z_$][\w$]*", code[:p])[-1]
    d, j = 0, p
    while j < len(code):
        if code[j] == "(":
            d += 1
        elif code[j] == ")":
            d -= 1
            if d == 0:
                break
        j += 1
    return name, param_types(code[p + 1:j])


def norm_text(t):
    return "\n".join(line.rstrip() for line in t.strip("\n").splitlines())


def select_members(members, specs):
    """Resolve target specs from targets.json against parsed members."""
    out = []
    for spec in specs:
        if spec == "*":
            return "ALL"
        if spec.startswith("#"):
            out += [m for m in members if m["kind"] == "field" and spec[1:] in m.get("names", [])]
            continue
        owner_sfx = None
        base = spec
        head = spec.split("(")[0].split("/")[0]
        if "." in head:
            owner_sfx, rest = spec.split(".", 1)
            base = rest
        mm = re.match(r"([\w$]+)(?:/(\d+)|\((.*)\))?$", base)
        if not mm:
            continue
        name, n, types = mm.group(1), mm.group(2), mm.group(3)
        c = [m for m in members if m["kind"] in ("method", "constructor") and m["name"] == name]
        if owner_sfx:
            c = [m for m in c if m["owner"].split(".")[-1] == owner_sfx]
        if n is not None:
            c = [m for m in c if len(m.get("params", [])) == int(n)]
        if types is not None:
            want = re.sub(r"\s+", "", types)
            c = [m for m in c if ",".join(m.get("params", [])) == want]
        out += [m for m in c if m not in out]
    out.sort(key=lambda m: m["start"])
    return out


def member_changes(path, old_src, new_src):
    """Compare two versions of one file member by member."""
    if old_src is None:
        return [{"status": "new file", "file": path, "member": "(whole file)", "old": None,
                 "new": {"start": 1, "end": new_src.count("\n") + 1, "text": new_src}}]
    if new_src is None:
        return [{"status": "deleted file", "file": path, "member": "(whole file)",
                 "old": {"start": 1, "end": old_src.count("\n") + 1, "text": old_src}, "new": None}]
    try:
        om, nm = parse_java(old_src), parse_java(new_src)
    except Exception:
        return [{"status": "changed", "file": path, "member": "(whole file - could not split into members)",
                 "old": {"start": 1, "end": old_src.count("\n") + 1, "text": old_src},
                 "new": {"start": 1, "end": new_src.count("\n") + 1, "text": new_src}}]
    od = {m["key"]: m for m in om}
    nd = {m["key"]: m for m in nm}
    out = []
    for m in nm:
        o = od.get(m["key"])
        if o is None:
            out.append({"status": "new", "file": path, "member": m["key"], "old": None, "new": _side(m)})
        elif norm_text(o["text"]) != norm_text(m["text"]):
            out.append({"status": "changed", "file": path, "member": m["key"], "old": _side(o), "new": _side(m)})
    for o in om:
        if o["key"] not in nd:
            out.append({"status": "removed", "file": path, "member": o["key"], "old": _side(o), "new": None})
    return out


def _side(m):
    return {"start": m["start"], "end": m["end"], "text": m["text"]}


def code_blob(changes, side):
    parts = []
    for c in changes:
        s = c[side]
        if not s:
            continue
        parts.append(f"// [{c['status']}] {Path(c['file']).name} > {c['member']}  (lines {s['start']}-{s['end']})\n{s['text'].rstrip()}\n")
    return "\n".join(parts)


# ======================================================================================
# tests (Maven + surefire reports) and public API snapshot (javap)
# ======================================================================================
def parse_surefire(report_dir):
    res = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "cases": {}, "classes": {}}
    for xf in sorted(Path(report_dir).glob("TEST-*.xml")):
        try:
            root = ET.parse(xf).getroot()
        except ET.ParseError:
            continue
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        for suite in suites:
            for tc in suite.iter("testcase"):
                cid = f"{tc.get('classname', '')}#{tc.get('name', '')}"
                if tc.find("failure") is not None:
                    st = "failed"
                elif tc.find("error") is not None:
                    st = "error"
                elif tc.find("skipped") is not None:
                    st = "skipped"
                else:
                    st = "passed"
                res["cases"][cid] = st
    for cid, st in res["cases"].items():
        cls = cid.split("#")[0].split(".")[-1]
        c = res["classes"].setdefault(cls, {"total": 0, "passed": 0})
        c["total"] += 1
        c["passed"] += st == "passed"
        res["total"] += 1
        res[{"passed": "passed", "failed": "failed", "error": "errors", "skipped": "skipped"}[st]] += 1
    return res


def run_tests(ws, only=None):
    cmd = [CFG["maven_cmd"]] + CFG["maven_args"] + CFG.get("maven_extra_args", [])
    if only:
        cmd += [f"-Dtest={only}", "-Dsurefire.failIfNoSpecifiedTests=false"]
    print(f"  running: {' '.join(cmd)}  (in {rel(ws)}) ...", flush=True)
    t0 = time.time()
    p = run(cmd, cwd=ws, timeout=int(CFG.get("test_timeout_minutes", 30)) * 60)
    log = p.stdout or ""
    res = parse_surefire(Path(ws) / "target" / "surefire-reports")
    compile_failed = "COMPILATION ERROR" in log or "Compilation failure" in log
    res["build_ok"] = res["total"] > 0 and not compile_failed
    res["maven_exit_code"] = p.returncode
    res["seconds"] = round(time.time() - t0, 1)
    res["only"] = only
    res["compile_errors"] = [line for line in log.splitlines() if line.startswith("[ERROR]") and ".java:[" in line][:40]
    if res["total"] == 0 and not compile_failed:
        tail = "\n".join(log.splitlines()[-25:])
        warn("Maven produced no test reports. Last lines of the Maven log:\n" + tail)
    return res, log


def test_line(r):
    if not r:
        return "not run"
    if not r.get("build_ok"):
        return "BUILD FAILED (did not compile or no tests ran)"
    extra = []
    for k in ("failed", "errors", "skipped"):
        if r.get(k):
            extra.append(f"{r[k]} {k}")
    return f"{r['passed']} passed of {r['total']}" + (f" ({', '.join(extra)})" if extra else "")


def api_snapshot(ws):
    cls_dir = Path(ws) / "target" / "classes"
    files = sorted(str(p) for p in cls_dir.rglob("*.class"))
    if not files:
        return None
    p = run(["javap", "-protected"] + files)
    api, cur, public = set(), None, False
    for line in (p.stdout or "").splitlines():
        s = line.strip()
        if not s or s.startswith(("Compiled from", "Picked up", "Warning")):
            continue
        if s.endswith("{") and ("class " in s or "interface " in s or "enum " in s):
            cur = s[:-1].strip()
            public = cur.startswith("public")
            if public:
                api.add(cur)
            continue
        if s == "}":
            cur = None
            continue
        if cur and public and s.startswith(("public", "protected")):
            name = re.search(r"(?:class|interface|enum)\s+([\w.$]+)", cur)
            api.add(f"{name.group(1) if name else cur} :: {s.rstrip(';')}")
    return sorted(api)


# ======================================================================================
# workspace
# ======================================================================================
def ensure_clone(llm):
    ws = ws_dir(llm)
    if (ws / ".git").exists():
        return ws
    ws.parent.mkdir(parents=True, exist_ok=True)
    print(f"  cloning {CFG['repo_url']} @ {CFG['tag']} into {rel(ws)} ...", flush=True)
    run(["git", "clone", "--quiet", "--depth", "1", "--branch", CFG["tag"], CFG["repo_url"], str(ws)], check=True)
    return ws


def tag_commit(ws):
    saved = ws.parent / "base_commit.txt"
    p = git(ws, "rev-parse", "-q", "--verify", f"refs/tags/{CFG['tag']}^{{commit}}", check=False)
    if p.returncode == 0 and p.stdout.strip():
        commit = p.stdout.strip()
    elif saved.exists():
        commit = read(saved).strip()
    else:
        die(f"cannot find tag {CFG['tag']} in {rel(ws)}; delete that folder and start again")
    write(saved, commit)
    return commit


def git_identity_args(ws):
    have = git(ws, "config", "user.email", check=False).stdout.strip()
    return [] if have else ["-c", "user.name=refactor-kit", "-c", "user.email=refactor-kit@localhost"]


# ======================================================================================
# rendering
# ======================================================================================
def tpl(name, **kw):
    text = read(KIT / "templates" / name)
    for k, v in kw.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def smell_table(s):
    rows = [("ID", s["id"]), ("Smell type", s["type"]), ("Code smell", s["smell"]), ("Class(es)", s["classes"]),
            ("Method / member", s["member"]), ("Lines (1.9.0)", s["lines"]), ("Priority", s["priority"])]
    out = "| Field | Value |\n|---|---|\n" + "\n".join(f"| {a} | {str(b).replace('|', '/')} |" for a, b in rows)
    out += f"\n\n**Evidence.** {s['evidence']}\n"
    return out


def technique_block(s):
    out = f"**Technique:** {s['technique']}\n\n"
    out += f"_Source: {s['technique_source']}._\n\n"
    if s["technique_how"]:
        out += f"**How (outline):** {s['technique_how']}\n\n"
    if s["risk"]:
        out += f"**Risks to watch:** {s['risk']}\n\n"
    if s["effect"]:
        out += f"**Expected effect on metrics:** {s['effect']}\n\n"
    if s["reviewer_notes"]:
        out += f"**Reviewer notes:** {s['reviewer_notes']}\n\n"
    return out


def target_excerpt(ws, s, base_commit):
    """Original code of the smell location, read from the base commit."""
    md, plain, listing = [], [], []
    for fname, specs in s["targets"].items():
        path = f"{SRC_ROOT}/{fname}"
        src = git(ws, "show", f"{base_commit}:{path}", check=False).stdout
        if not src:
            continue
        if not specs:
            listing.append(f"- `{path}` (file is involved; no specific member)")
            continue
        try:
            sel = select_members(parse_java(src), specs)
        except Exception:
            sel = "ALL"
        if sel == "ALL":
            n = src.count("\n") + 1
            listing.append(f"- `{path}` - whole file (lines 1-{n})")
            md.append(f"#### `{path}` (whole file, {n} lines - open it in the workspace)\n")
            plain.append(f"// {fname} (whole file, lines 1-{n})\n{src}")
            continue
        for m in sel:
            label = m["key"]
            listing.append(f"- `{path}` > `{label}` (lines {m['start']}-{m['end']})")
            md.append(f"#### `{fname}` > `{label}` (lines {m['start']}-{m['end']})\n\n```java\n{m['text'].rstrip()}\n```\n")
            plain.append(f"// [smell location] {fname} > {label}  (lines {m['start']}-{m['end']})\n{m['text'].rstrip()}\n")
    return "\n".join(listing), "\n".join(md), "\n".join(plain)


# ======================================================================================
# commands
# ======================================================================================
def cmd_check(_a):
    ok = True
    print(f"Kit folder: {KIT}")
    print(f"Python {sys.version.split()[0]}")
    try:
        import openpyxl
        print(f"openpyxl {openpyxl.__version__}")
    except ImportError:
        ok = False
        print("openpyxl  MISSING  -> pip install openpyxl")
    for tool, args in (("git", ["--version"]), ("java", ["-version"]), ("javac", ["-version"]), ("javap", ["-version"]),
                       (CFG["maven_cmd"], ["-v"])):
        exe = shutil.which(tool)
        if not exe:
            ok = False
            print(f"{tool:6}  MISSING")
            continue
        out = run([tool] + args).stdout or ""
        first = next((l for l in out.splitlines() if l.strip() and not l.startswith("Picked up")), "")
        print(f"{tool:6}  {first.strip()}")
    coords = metric_tool()["maven_coords"]
    _g, _a, _v = coords.split(":")
    ck_ok = (KIT / "tools" / "ck" / _v / "lib" / f"{_a}-{_v}.jar").exists()
    print(f"ck      {coords} {'(downloaded)' if ck_ok else '(not downloaded yet - `kit.py metrics` fetches it with Maven on first use)'}")
    sw = KIT / CFG["smells_workbook"]
    print(f"smells workbook: {rel(sw)} {'(found)' if sw.exists() else '(MISSING)'}")
    ok = ok and sw.exists()
    print("\nAll good." if ok else "\nSomething is missing - fix it before starting a run.")
    sys.exit(0 if ok else 1)


def cmd_show(a):
    s = get_smell(a.smell)
    print(f"\n{s['id']} - {s['smell']} ({s['type']}) - priority {s['priority']}")
    print(f"Class(es): {s['classes']}\nMember:    {s['member']}\nLines:     {s['lines']}\n")
    print("Evidence:\n  " + s["evidence"] + "\n")
    print(f"Refactoring to apply [{s['technique_source']}]:\n  {s['technique']}")
    if s["technique_how"]:
        print("How:\n  " + s["technique_how"])
    if s["risk"]:
        print("Risk:\n  " + s["risk"])
    if s["decision"]:
        print(f"Reviewer decision: {s['decision']}")
    if s["targets"]:
        print("Target files: " + ", ".join(s["targets"]))
    if s["tests"]:
        print("Most relevant tests: " + ", ".join(s["tests"]))


def cmd_start(a):
    s = get_smell(a.smell)
    if s["decision"].lower().startswith("reject") and not a.force:
        die(f"{s['id']} is marked 'Reject' in the review sheet. Pick another smell or use --force.")
    rd = run_dir(a.llm, s["id"])
    if (rd / "run.json").exists() and not a.force:
        die(f"{rel(rd)} already exists. Use --force to start over (this deletes that run folder).")
    if rd.exists() and a.force:
        shutil.rmtree(rd)
    rd.mkdir(parents=True)

    print(f"\n[1/6] Workspace for {a.llm}")
    ws = ensure_clone(a.llm)
    tagc = tag_commit(ws)
    base_ref = a.base or CFG["tag"]
    base_commit = tagc if not a.base else git(ws, "rev-parse", a.base).stdout.strip()
    branch = f"refactor/{s['id']}"
    dirty = git(ws, "status", "--porcelain", check=False).stdout.strip()
    if dirty:
        cur = git(ws, "rev-parse", "--abbrev-ref", "HEAD", check=False).stdout.strip()
        warn(f"discarding uncommitted changes on {cur} (an unfinished run?)")
    git(ws, "checkout", "--quiet", "-f", "-B", branch, base_commit)
    git(ws, "clean", "-fdq")
    print(f"  {rel(ws)} on branch {branch} at {base_commit[:10]} ({base_ref})")

    print("[2/6] Saving the original code")
    for fname in s["targets"]:
        path = f"{SRC_ROOT}/{fname}"
        if (ws / path).exists():
            dst = rd / "original" / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ws / path, dst)
    listing, excerpt_md, excerpt_plain = target_excerpt(ws, s, base_commit)
    write(rd / "original_smell_location.java.txt", excerpt_plain)
    print(f"  {rel(rd / 'original')}/ and original_smell_location.java.txt")

    print("[3/6] Running the original tests on the untouched code")
    cache = KIT / "workspace" / ".baseline" / base_commit
    if (cache / "tests.json").exists() and not a.fresh_baseline:
        base_res = json.loads(read(cache / "tests.json"))
        shutil.copy2(cache / "tests.log", rd / "tests_original.log")
        api = json.loads(read(cache / "api.json"))
        print(f"  reused cached baseline for {base_commit[:10]} (use --fresh-baseline to re-run)")
    else:
        base_res, log = run_tests(ws)
        api = api_snapshot(ws) or []
        cache.mkdir(parents=True, exist_ok=True)
        write(cache / "tests.json", json.dumps(base_res, indent=1))
        write(cache / "tests.log", log)
        write(cache / "api.json", json.dumps(api))
        write(rd / "tests_original.log", log)
    write(rd / "tests_original.json", json.dumps(base_res, indent=1))
    write(rd / "api_original.txt", "\n".join(api))
    print(f"  Original tests: {test_line(base_res)}")
    if not base_res.get("build_ok") or base_res["failed"] or base_res["errors"]:
        warn("the ORIGINAL code does not pass all tests on this machine. Fix the environment before refactoring "
             "(see tests_original.log); results would not be comparable.")

    print("[4/6] Writing the task files")
    rules = tpl("RULES.md", SMELL_ID=s["id"], LLM_SLUG=slug(a.llm))
    common = dict(SMELL_ID=s["id"], SMELL_NAME=s["smell"], SMELL_TYPE=s["type"], LLM_NAME=a.llm, LLM_SLUG=slug(a.llm),
                  MODEL=a.model, MODE=a.mode, DATE=now(), TAG=CFG["tag"], BASE_REF=base_ref, BASE_SHORT=base_commit[:10],
                  BRANCH=branch, WORKSPACE=rel(ws), RUN_DIR=rel(rd), SMELL_TABLE=smell_table(s),
                  TECHNIQUE=technique_block(s), TARGET_LIST=listing or "- (see the smell row)", TARGET_CODE=excerpt_md,
                  TESTS=", ".join(s["tests"]) or "(full suite)", FIRST_TEST=(s["tests"] or ["HelpFormatterTest"])[0],
                  RULES=rules, SOURCE_ROOT=SRC_ROOT)
    write(rd / "TASK.md", tpl("TASK.md", **common))
    files_md = []
    for fname in s["targets"]:
        path = f"{SRC_ROOT}/{fname}"
        if (ws / path).exists():
            files_md.append(f"### FILE: {path}\n\n```java\n{read(ws / path).rstrip()}\n```\n")
    pkg_files = ", ".join(sorted(p.name for p in (ws / SRC_ROOT).glob("*.java")))
    write(rd / "CHAT_PROMPT.md", tpl("CHAT_PROMPT.md", **common, SOURCE_FILES="\n".join(files_md), PACKAGE_FILES=pkg_files))
    write(rd / "process.md", tpl("process.md", **common))
    shutil.copy2(KIT / "PROMPT.md", rd / "PROMPT_master.md")

    print("[5/6] Recording the run")
    meta = {"smell": s["id"], "smell_name": s["smell"], "smell_type": s["type"], "classes": s["classes"],
            "member": s["member"], "lines": s["lines"], "technique": s["technique"], "technique_source": s["technique_source"],
            "llm": a.llm, "llm_slug": slug(a.llm), "model": a.model, "mode": a.mode, "base_ref": base_ref,
            "base_commit": base_commit, "branch": branch, "workspace": rel(ws), "started": now(), "status": "started",
            "finish_attempts": 0}
    save_run(rd, meta)
    rebuild_log()

    print("[6/6] Done.\n")
    if a.mode == "chat":
        print("NEXT (chat mode):\n"
              f"  1. Open a NEW chat with {a.llm} and paste (or attach) {rel(rd / 'CHAT_PROMPT.md')}\n"
              f"  2. Save its complete reply as {rel(rd / 'response.md')}\n"
              f"  3. python kit.py apply  --smell {s['id']} --llm \"{a.llm}\"\n"
              f"  4. python kit.py finish --smell {s['id']} --llm \"{a.llm}\"")
    else:
        print("NEXT (agent mode):\n"
              f"  Read {rel(rd / 'TASK.md')} completely, fill sections 1-2 of {rel(rd / 'process.md')},\n"
              f"  refactor inside {rel(ws)}, testing after each step with\n"
              f"    python kit.py test --llm \"{a.llm}\" --only {common['FIRST_TEST']}\n"
              f"  then complete process.md and run\n"
              f"    python kit.py finish --smell {s['id']} --llm \"{a.llm}\"")


def cmd_test(a):
    ws = ws_dir(a.llm)
    if not (ws / ".git").exists():
        die(f"no workspace for {a.llm}; run `kit.py start` first")
    res, log = run_tests(ws, only=a.only)
    write(ws.parent / "last_test.log", log)
    print(f"\nTests{' (' + a.only + ')' if a.only else ''}: {test_line(res)}  [{res['seconds']}s]")
    bad = [c for c, st in res["cases"].items() if st in ("failed", "error")]
    for c in bad[:30]:
        print("  FAILED: " + c)
    for e in res["compile_errors"][:15]:
        print("  " + e)
    print(f"Full Maven log: {rel(ws.parent / 'last_test.log')}")
    sys.exit(0 if res["build_ok"] and not bad else 1)


FILE_BLOCK = re.compile(r"^#{2,4}\s*FILE:\s*`?([^\s`]+)`?\s*$\s*^(```|~~~)[^\n]*\n(.*?)^\2\s*$", re.M | re.S)
TRUNCATION_HINTS = re.compile(r"^\s*(//|/\*|\*)?\s*(\.\.\.|…)\s*(\*/)?\s*$|rest of (the )?(file|class|code|method)|"
                              r"(remains?|stays?) (the same|unchanged)|existing (code|methods)|unchanged (code|methods?|members?)", re.I | re.M)


def cmd_apply(a):
    rd, meta = load_run(a.llm, a.smell)
    ws = KIT / meta["workspace"]
    resp = Path(a.response) if a.response else rd / "response.md"
    if not resp.is_absolute():
        resp = (Path.cwd() / resp) if (Path.cwd() / resp).exists() else rd / resp
    if not resp.exists():
        die(f"response file not found: {resp}")
    text = read(resp)
    blocks = FILE_BLOCK.findall(text)
    if not blocks:
        die("no '### FILE: <path>' blocks with code fences found in the response. Check the output format in CHAT_PROMPT.md.")
    written = []
    for path, _fence, body in blocks:
        path = path.strip().lstrip("./")
        if path.endswith("/Example.java") and body.strip().startswith("(the COMPLETE content"):
            continue  # the format example from the prompt, pasted along with the reply
        if not path.startswith(SRC_ROOT + "/") or not path.endswith(".java"):
            warn(f"skipping {path}: only files under {SRC_ROOT}/ may be changed")
            continue
        dst = (ws / path).resolve()
        if ws.resolve() not in dst.parents:
            warn(f"skipping {path}: outside the workspace")
            continue
        old = read(dst) if dst.exists() else None
        problems = []
        if old and len(body.splitlines()) < 0.6 * len(old.splitlines()):
            problems.append(f"much shorter than the original ({len(body.splitlines())} vs {len(old.splitlines())} lines)")
        hits = [m.group(0).strip() for m in TRUNCATION_HINTS.finditer(body)]
        if hits:
            problems.append(f"placeholder text {hits[:3]}")
        if problems and not a.force:
            warn(f"NOT written: {path} looks incomplete: {'; '.join(problems)}. Ask the LLM for the complete file, "
                 f"or re-run apply with --force if the file really is complete.")
            continue
        if problems:
            warn(f"{path}: {'; '.join(problems)} (written anyway because of --force)")
        write(dst, body if body.endswith("\n") else body + "\n")
        if path not in written:
            written.append(path)
    m = re.search(r"^##\s*Refactoring process\s*$(.*?)(?=^##\s*Changed files\s*$|\Z)", text, re.M | re.S)
    if m and m.group(1).strip():
        write(rd / "process.md", f"# Refactoring process - {meta['smell']} {meta['smell_name']} - {meta['llm']}\n\n"
                                 f"_Taken from the LLM reply ({resp.name})._\n\n{m.group(1).strip()}\n")
        print(f"  process.md written from the reply")
    else:
        warn("no '## Refactoring process' section found in the reply; process.md left as is")
    if resp.parent != rd:
        shutil.copy2(resp, rd / resp.name)
    meta.setdefault("responses", [])
    if resp.name not in meta["responses"]:
        meta["responses"].append(resp.name)
    save_run(rd, meta)
    print("Applied files:\n  " + "\n  ".join(written))
    print(f"\nNext: python kit.py finish --smell {meta['smell']} --llm \"{meta['llm']}\"")


def cmd_finish(a):
    rd, meta = load_run(a.llm, a.smell)
    ws = KIT / meta["workspace"]
    base = meta["base_commit"]
    cur_branch = git(ws, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if cur_branch != meta["branch"]:
        die(f"workspace is on branch {cur_branch}, expected {meta['branch']}")

    print("\n[1/6] Collecting the changes")
    git(ws, "add", "-A")
    status = git(ws, "diff", "--cached", "--name-status", "--no-renames", base).stdout.strip().splitlines()
    changes = []
    for line in status:
        parts = line.split("\t")
        changes.append((parts[0][0], parts[-1]))
    if not changes:
        warn("no changes found in the workspace compared to the original code")
    numstat = {}
    for line in git(ws, "diff", "--cached", "--numstat", "--no-renames", base).stdout.splitlines():
        p = line.split("\t")
        if len(p) == 3:
            numstat[p[2]] = (int(p[0]) if p[0].isdigit() else 0, int(p[1]) if p[1].isdigit() else 0)
    write(rd / "changes.patch", git(ws, "diff", "--cached", "--no-renames", base).stdout)
    test_files = [p for _, p in changes if p.startswith("src/test/")]
    other_files = [p for _, p in changes if not p.startswith(SRC_ROOT + "/") and not p.startswith("src/test/")]
    for d in ("refactored",):
        if (rd / d).exists():
            shutil.rmtree(rd / d)
    code_changes = []
    for st, path in changes:
        old = git(ws, "show", f"{base}:{path}", check=False).stdout if st != "A" else None
        new = read(ws / path) if st != "D" and (ws / path).exists() else None
        if old is not None and st != "A":
            dst = rd / "original" / path
            if not dst.exists():
                write(dst, old)
        if new is not None:
            write(rd / "refactored" / path, new)
        if path.endswith(".java"):
            code_changes += member_changes(path, old, new)
    write(rd / "code_changes.json", json.dumps(code_changes, indent=1))
    added = sum(v[0] for v in numstat.values())
    removed = sum(v[1] for v in numstat.values())
    print(f"  {len(changes)} file(s) changed, +{added} -{removed} lines, {len(code_changes)} member change(s)")

    print("[2/6] Running the original tests on the refactored code")
    res, log = run_tests(ws)
    write(rd / "tests_refactored.json", json.dumps(res, indent=1))
    write(rd / "tests_refactored.log", log)
    base_res = json.loads(read(rd / "tests_original.json"))
    regress = sorted(c for c, st in base_res["cases"].items() if st == "passed" and res["cases"].get(c) != "passed")
    print(f"  Original tests:   {test_line(base_res)}")
    print(f"  Refactored tests: {test_line(res)}  -> regressions: {len(regress)}")

    print("[3/6] Comparing the public/protected API")
    api_old = [l for l in read(rd / "api_original.txt").splitlines() if l.strip()]
    api_new = api_snapshot(ws) if res["build_ok"] else None
    if api_new is None:
        api_removed, api_added = [], []
        write(rd / "api_diff.txt", "API not compared: the refactored code did not compile.\n")
    else:
        write(rd / "api_refactored.txt", "\n".join(api_new))
        so, sn = set(api_old), set(api_new)
        api_removed, api_added = sorted(so - sn), sorted(sn - so)
        write(rd / "api_diff.txt", "REMOVED or changed (breaking):\n" + "\n".join("- " + x for x in api_removed) +
              "\n\nADDED:\n" + "\n".join("+ " + x for x in api_added) + "\n")
    print(f"  removed/changed: {len(api_removed)}, added: {len(api_added)}")

    print("[4/6] Committing the refactoring on the run branch")
    if changes:
        msg = f"{meta['smell']} {meta['smell_name']}: refactoring by {meta['llm']} ({meta['model']})"
        git(ws, *git_identity_args(ws), "commit", "--quiet", "-m", msg, check=False)
    commit = git(ws, "rev-parse", "HEAD").stdout.strip()

    reasons = []
    if not res["build_ok"]:
        reasons.append("build failed")
    if regress:
        reasons.append(f"{len(regress)} regression(s)")
    if test_files:
        reasons.append("test files modified")
    if api_removed:
        reasons.append(f"{len(api_removed)} public/protected API element(s) removed or changed")
    if not changes:
        reasons.append("no code changes")
    verdict = "PASS" if not reasons else "REVIEW"

    proc = read(rd / "process.md") if (rd / "process.md").exists() else ""
    guidance = [l.strip() for l in read(KIT / "templates" / "process.md").splitlines()
                if re.search(r"_[^_]{6,}_", l) and "{{" not in l and not l.startswith(">")]
    proc_lines = {l.strip() for l in proc.splitlines()}
    leftover = sum(1 for g in guidance if g in proc_lines)
    if leftover:
        warn(f"process.md still has {leftover} line(s) of template guidance - the LLM should complete it.")

    meta.update({"status": "finished", "finished": now(), "finish_attempts": meta.get("finish_attempts", 0) + 1,
                 "commit": commit, "verdict": verdict, "verdict_reasons": reasons,
                 "files_changed": [f"{p} (+{numstat.get(p, (0, 0))[0]} -{numstat.get(p, (0, 0))[1]})" for _, p in changes],
                 "lines_added": added, "lines_removed": removed,
                 "members": {k: sum(1 for c in code_changes if c["status"] == k) for k in ("changed", "new", "removed", "new file", "deleted file")},
                 "regressions": regress, "test_files_modified": test_files, "other_files_modified": other_files,
                 "api_removed": api_removed, "api_added": api_added, "process_template_lines_left": leftover})
    save_run(rd, meta)

    print("[5/6] Writing REPORT.md")
    write(rd / "REPORT.md", build_report(rd, meta, base_res, res, code_changes))

    print("[6/6] Updating the Excel log")
    rebuild_log()
    print(f"\nVERDICT: {verdict}" + (f"  ({'; '.join(reasons)})" if reasons else ""))
    print(f"Report: {rel(rd / 'REPORT.md')}\nLog:    {CFG['log_workbook']}")


def cmd_log(_a):
    rebuild_log()


def cmd_status(_a):
    runs = all_runs()
    if not runs:
        print("No runs yet.")
        return
    print(f"{'Run':28} {'Status':9} {'Verdict':8} {'Original':>10} {'Refactored':>11}  Started")
    for rd, m in runs:
        o = _load_json(rd / "tests_original.json")
        r = _load_json(rd / "tests_refactored.json")
        fmt = lambda x: f"{x['passed']}/{x['total']}" if x else "-"
        print(f"{m['smell'] + ' / ' + m['llm']:28} {m['status']:9} {m.get('verdict', '-'):8} {fmt(o):>10} {fmt(r):>11}  {m['started']}")


# ======================================================================================
# report
# ======================================================================================
def _load_json(p):
    return json.loads(read(p)) if Path(p).exists() else None


def build_report(rd, m, base_res, res, changes):
    L = []
    L.append(f"# Refactoring report - {m['smell']} {m['smell_name']} - {m['llm']}\n")
    L.append("| | |\n|---|---|")
    rows = [("Smell", f"{m['smell']} - {m['smell_name']} ({m['smell_type']})"),
            ("Class / member", f"{m['classes']} - {m['member']} (lines {m['lines']})"),
            ("Refactoring applied", m["technique"]),
            ("LLM / model", f"{m['llm']} - {m['model']}"), ("Mode", m["mode"]),
            ("Code base", f"{m['base_ref']} ({m['base_commit'][:10]}) -> branch `{m['branch']}` commit {m.get('commit', '')[:10]}"),
            ("Verdict", f"**{m['verdict']}**" + (f" - {'; '.join(m['verdict_reasons'])}" if m["verdict_reasons"] else "")),
            ("Original tests", test_line(base_res)),
            ("Refactored tests", f"{test_line(res)} - regressions: {len(m['regressions'])}"),
            ("Test files modified", "Yes: " + ", ".join(m["test_files_modified"]) if m["test_files_modified"] else "No"),
            ("Public/protected API", f"{len(m['api_removed'])} removed or changed, {len(m['api_added'])} added"),
            ("Files changed", "<br>".join(m["files_changed"]) or "none"),
            ("Finish attempts", str(m["finish_attempts"]))]
    L += [f"| {a} | {str(b).replace('|', '/')} |" for a, b in rows]

    s = None
    try:
        s = get_smell(m["smell"])
    except SystemExit:
        pass
    L.append("\n## 1. Smell (from the review sheet)\n")
    if s:
        L.append(f"**Evidence.** {s['evidence']}\n")
        L.append(technique_block(s))

    L.append("## 2. Original code (before refactoring)\n")
    L.append("_Every member the refactoring changed or removed, as it was in the original code. Full files: `original/`._\n")
    L += _code_sections(changes, "old") or ["_No members changed._\n"]

    L.append("## 3. Original tests (on the untouched code)\n")
    L.append(f"- Result: **{test_line(base_res)}**\n- Log: `tests_original.log`\n")

    L.append("## 4. Refactoring process\n")
    proc = read(rd / "process.md") if (rd / "process.md").exists() else "_process.md missing_"
    proc = re.sub(r"^# .*\n", "", proc, count=1)
    L.append(re.sub(r"^(#{2,5}) ", lambda mm: "#" + mm.group(1) + " ", proc, flags=re.M).strip() + "\n")

    L.append("## 5. Refactored code (after refactoring)\n")
    L.append("_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._\n")
    L += _code_sections(changes, "new") or ["_No members changed._\n"]

    L.append("## 6. Original tests on the refactored code\n")
    L.append(f"- Result: **{test_line(res)}**\n- Regressions (passed before, not now): **{len(m['regressions'])}**\n- Log: `tests_refactored.log`\n")
    if res.get("compile_errors"):
        L.append("Compilation errors:\n\n```\n" + "\n".join(res["compile_errors"]) + "\n```\n")
    if m["regressions"]:
        L.append("Regressions:\n\n" + "\n".join(f"- `{c}`" for c in m["regressions"][:100]) + "\n")
    classes = sorted(set(base_res.get("classes", {})) | set(res.get("classes", {})))
    if classes:
        L.append("| Test class | Original (passed/total) | Refactored (passed/total) |\n|---|---|---|")
        for c in classes:
            o = base_res.get("classes", {}).get(c)
            r = res.get("classes", {}).get(c)
            f = lambda x: f"{x['passed']}/{x['total']}" if x else "-"
            flag = "" if (o and r and o == r) else " **<-**"
            L.append(f"| {c} | {f(o)} | {f(r)}{flag} |")
        L.append("")

    L.append("## 7. Checks\n")
    L.append(f"- Test files untouched: {'NO - ' + ', '.join(m['test_files_modified']) if m['test_files_modified'] else 'yes'}")
    L.append(f"- Other non-source files changed: {', '.join(m['other_files_modified']) or 'none'}")
    L.append(f"- Public/protected API removed or changed: {len(m['api_removed'])}" +
             ("".join(f"\n  - `{x}`" for x in m["api_removed"][:30])))
    L.append(f"- Public/protected API added: {len(m['api_added'])}" + ("".join(f"\n  - `{x}`" for x in m["api_added"][:30])))
    if m.get("process_template_lines_left"):
        L.append(f"- process.md still had {m['process_template_lines_left']} line(s) of template guidance")
    L.append("\n## 8. Files in this run folder\n")
    L.append("| File | What it is |\n|---|---|")
    files = [("PROMPT_master.md", "the unified prompt (master copy at start)"),
             ("TASK.md / CHAT_PROMPT.md", "the run-specific task given to the LLM (agent / chat mode)"),
             ("response*.md", "the LLM's reply / transcript (saved by you)"),
             ("process.md", "the refactoring process written by the LLM"),
             ("original/", "original versions of every involved file"),
             ("original_smell_location.java.txt", "original code of the smell location"),
             ("refactored/", "refactored versions of every changed file"),
             ("changes.patch", "unified diff against the original"),
             ("code_changes.json", "member-by-member before/after"),
             ("tests_original.json/.log", "original test suite on the original code"),
             ("tests_refactored.json/.log", "original test suite on the refactored code"),
             ("api_original.txt / api_refactored.txt / api_diff.txt", "public/protected API comparison"),
             ("run.json", "run metadata")]
    L += [f"| `{a}` | {b} |" for a, b in files]
    return "\n".join(L) + "\n"


def _code_sections(changes, side):
    out = []
    for c in changes:
        s = c[side]
        if not s:
            continue
        out.append(f"### [{c['status']}] `{Path(c['file']).name}` > `{c['member']}` (lines {s['start']}-{s['end']})\n\n```java\n{s['text'].rstrip()}\n```\n")
    return out


# ======================================================================================
# metrics (CK, the same tool and the same settings for every run)
# ======================================================================================
DEFAULT_METRIC_TOOL = {
    "maven_coords": "com.github.mauricioaniche:ck:0.7.0",
    "definitions": {
        "Size": {"ck": "loc", "aggregate": "sum", "label": "LOC (CK loc)"},
        "Cohesion": {"ck": "lcom*", "aggregate": "mean", "label": "LCOM* (CK lcom*, Henderson-Sellers; 0 = cohesive, 1 = no cohesion)"},
        "Coupling": {"ck": "cbo", "aggregate": "sum", "label": "CBO (CK cbo)"},
    },
}
CK_CLASS_COLS = ["loc", "wmc", "cbo", "rfc", "lcom", "lcom*", "tcc", "totalMethodsQty"]
CK_METHOD_COLS = ["loc", "wmc", "parametersQty", "cbo"]
CLASS_RULE = ("the top-level class of every affected file (the smell's target files plus the source files the run changed), "
              "plus any other class in those files that holds a target member, is new or removed, or whose CK metrics changed")


def metric_tool():
    mt = dict(DEFAULT_METRIC_TOOL)
    mt.update(CFG.get("metric_tool", {}))
    return mt


def ensure_ck():
    """Download CK and its dependencies once with Maven (same Maven settings as the tests); return the lib folder."""
    coords = metric_tool()["maven_coords"]
    g, a, v = coords.split(":")
    home = KIT / "tools" / "ck" / v
    lib = home / "lib"
    if (lib / f"{a}-{v}.jar").exists():
        return lib
    print(f"  downloading {coords} and its dependencies with Maven (first use only) ...")
    write(home / "pom.xml", (
        '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>'
        '<groupId>kit</groupId><artifactId>ck-download</artifactId><version>1</version><packaging>pom</packaging>'
        f'<dependencies><dependency><groupId>{g}</groupId><artifactId>{a}</artifactId><version>{v}</version>'
        '</dependency></dependencies></project>\n'))
    p = run([CFG["maven_cmd"], "-B", "-q", *CFG.get("maven_extra_args", []), "dependency:copy-dependencies",
             f"-DoutputDirectory={lib}"], cwd=home, timeout=CFG.get("test_timeout_minutes", 30) * 60)
    if not (lib / f"{a}-{v}.jar").exists():
        die(f"could not download {coords} with Maven:\n{(p.stdout or '')[-3000:]}")
    return lib


def _read_csv(p):
    import csv
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ck_measure(ws, commit, lib):
    """Run CK on src/main/java of one commit (exported with git archive). Cached per CK version and commit."""
    v = metric_tool()["maven_coords"].split(":")[-1]
    cache = KIT / "workspace" / ".ck" / v / commit
    cls_csv, mth_csv = cache / "class.csv", cache / "method.csv"
    if not (cls_csv.exists() and mth_csv.exists()):
        import tarfile
        src = cache / "src"
        shutil.rmtree(src, ignore_errors=True)
        src.mkdir(parents=True)
        tar = cache / "src.tar"
        git(ws, "archive", "--format=tar", "-o", str(tar), commit, "src/main/java")
        with tarfile.open(tar) as tf:
            if hasattr(tarfile, "data_filter"):
                tf.extractall(src, filter="data")
            else:
                tf.extractall(src)
        tar.unlink()
        print(f"  running CK on {commit[:10]} ...")
        p = run(["java", "-cp", str(lib / "*"), "com.github.mauricioaniche.ck.Runner", str(src), "false", "0", "false",
                 str(cache) + os.sep], cwd=cache, timeout=600)
        shutil.rmtree(src, ignore_errors=True)
        if not (cls_csv.exists() and mth_csv.exists()):
            die(f"CK produced no output for {commit[:10]}:\n{(p.stdout or '')[-3000:]}")
    return _read_csv(cls_csv), _read_csv(mth_csv)


def _ck_rel(path):
    p = path.replace("\\", "/")
    i = p.rfind("src/main/java/")
    return p[i:] if i >= 0 else p


def _split_top(s):
    """Split a parameter list at top-level commas (not inside <...>)."""
    out, depth, cur = [], 0, ""
    for ch in s:
        depth += (ch == "<") - (ch == ">")
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out]


def _simple_type(t):
    t = re.sub(r"<.*>", "", t.replace("...", "[]")).strip()
    return re.split(r"[.$]", t)[-1]


def _ck_method(sig):
    """'appendOptions/5[A,int,org.x.Options,int,int]' -> ('appendOptions', 5, ['A', 'int', 'Options', 'int', 'int'])."""
    mm = re.match(r"^([^/]+)/(\d+)(?:\[(.*)\])?$", sig)
    if not mm:
        return sig, None, []
    return mm.group(1), int(mm.group(2)), [_simple_type(t) for t in _split_top(mm.group(3) or "")]


def _spec_matches(spec, cls, sig):
    """A targets.json member spec (name | name/N | name(Type,..) | Owner.name) against a CK class + method."""
    sm = re.match(r"^(?:([A-Za-z_$][\w$]*)\.)?([A-Za-z_$][\w$]*)(?:/(\d+)|\((.*)\))?$", spec.strip())
    if not sm:
        return False  # '#field' and '*' have no method rows
    owner, name, n, types = sm.groups()
    parts = cls.rsplit(".", 1)[-1].split("$")
    if (owner and parts[-1] != owner) or (not owner and len(parts) > 1):
        return False
    mname, mn, mtypes = _ck_method(sig)
    if mname != name or (n is not None and mn != int(n)):
        return False
    return types is None or mtypes == [_simple_type(t) for t in _split_top(types)]


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x:  # NaN
        return None
    return int(x) if x.is_integer() else round(x, 4)


def _aggregate(vals, how):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    if how == "mean":
        return round(sum(vals) / len(vals), 4)
    s = sum(vals)
    return round(s, 4) if isinstance(s, float) else s


def measure_run(rd, m):
    """Measure one finished run before/after with CK; write metrics.json + metrics.md; return the summary values."""
    mt = metric_tool()
    defs = mt["definitions"]
    ws = KIT / m["workspace"]
    lib = ensure_ck()
    before = ck_measure(ws, m["base_commit"], lib)
    after = ck_measure(ws, m["commit"], lib)
    targets = load_targets().get(m["smell"], {}).get("targets", {})
    specs = {f"{SRC_ROOT}/{f}": v for f, v in targets.items()}
    files = set(specs)
    for fc in m.get("files_changed", []):
        p = fc.rsplit(" (", 1)[0].strip()
        if p.startswith("src/main/java/") and p.endswith(".java"):
            files.add(p)
    cols = CK_CLASS_COLS + [d["ck"] for d in defs.values() if d["ck"] not in CK_CLASS_COLS]
    bc = {r["class"]: r for r in before[0] if _ck_rel(r["file"]) in files}
    ac = {r["class"]: r for r in after[0] if _ck_rel(r["file"]) in files}
    bm = {(r["class"], r["method"]): r for r in before[1] if r["class"] in bc}
    am = {(r["class"], r["method"]): r for r in after[1] if r["class"] in ac}

    def vals(r, cs):
        return {c: _num(r.get(c)) for c in cs} if r else None

    methods = []
    for key in set(bm) | set(am):
        b, a_ = bm.get(key), am.get(key)
        file = _ck_rel((b or a_)["file"])
        if any(_spec_matches(s, key[0], key[1]) for s in specs.get(file, [])):
            status = "target"
        elif not b:
            status = "new"
        elif not a_:
            status = "removed"
        elif vals(b, CK_METHOD_COLS) != vals(a_, CK_METHOD_COLS):
            status = "changed"
        else:
            continue
        methods.append({"class": key[0], "method": key[1], "status": status, "line": int((a_ or b)["line"]),
                        "before": vals(b, CK_METHOD_COLS), "after": vals(a_, CK_METHOD_COLS)})
    methods.sort(key=lambda x: (x["class"], x["line"]))

    target_classes = {x["class"] for x in methods if x["status"] == "target"}
    classes = []
    for name in sorted(set(bc) | set(ac)):
        b, a_ = bc.get(name), ac.get(name)
        file = _ck_rel((b or a_)["file"])
        top = name.rsplit(".", 1)[-1] == Path(file).stem
        counted = top or name in target_classes or not (b and a_) or vals(b, cols) != vals(a_, cols)
        classes.append({"class": name, "file": file, "counted": counted, "before": vals(b, cols), "after": vals(a_, cols)})

    summary = {}
    for name in CFG.get("metrics", []):
        d = defs.get(name)
        if not d:
            continue
        how = d.get("aggregate", "sum")
        bv = _aggregate([c["before"][d["ck"]] for c in classes if c["counted"] and c["before"]], how)
        av = _aggregate([c["after"][d["ck"]] for c in classes if c["counted"] and c["after"]], how)
        ch = None if bv is None or av is None else (round(av - bv, 4) if isinstance(av - bv, float) else av - bv)
        summary[name] = {"before": bv, "after": av, "change": ch, "ck": d["ck"], "aggregate": how, "label": d.get("label", d["ck"])}

    res = {"run": f"{m['smell']} - {m['llm']}", "tool": mt["maven_coords"], "measured": now(),
           "before_commit": m["base_commit"], "after_commit": m["commit"], "files": sorted(files),
           "class_rule": CLASS_RULE, "metrics": summary, "classes": classes, "methods": methods}
    write(rd / "metrics.json", json.dumps(res, indent=1))
    write(rd / "metrics.md", metrics_md(m, res))
    return res


def _fmt(v):
    return "-" if v is None else (f"{v:.4g}" if isinstance(v, float) else str(v))


def _ba(b, a):
    """'b' when equal, 'b → a' when changed, '- → a' / 'b → -' for new / removed."""
    if b == a:
        return _fmt(b)
    return f"{_fmt(b)} → {_fmt(a)}"


def _delta(b, a):
    if b is None or a is None:
        return "-"
    d = a - b
    d = round(d, 4) if isinstance(d, float) else d
    return ("+" if d > 0 else "") + _fmt(d)


def metrics_md(m, res):
    short = lambda c: c.rsplit(".", 1)[-1]
    L = [f"# Metrics - {m['smell']} {m.get('smell_name', '')} - {m['llm']}", "",
         f"Measured with **CK** (`{res['tool']}`) on the whole `src/main/java` tree. Before = `{res['before_commit'][:10]}` "
         f"(original), after = `{res['after_commit'][:10]}` (branch `{m.get('branch', '')}`). Measured {res['measured']} by `python kit.py metrics`.", "",
         f"**Classes counted:** {res['class_rule']}.", "",
         "Affected files: " + ", ".join(f"`{f.rsplit('/', 1)[-1]}`" for f in res["files"]), "",
         "## Summary (these values are written to the Metrics sheet)", "",
         "| Metric | Measure | Before | After | Change |", "|---|---|---:|---:|---:|"]
    for name, v in res["metrics"].items():
        L.append(f"| {name} | {v['label']}, {v['aggregate']} over the counted classes | {_fmt(v['before'])} | {_fmt(v['after'])} | {_delta(v['before'], v['after'])} |")
    cols = CK_CLASS_COLS
    L += ["", "## Per class (before → after)", "",
          "| Class | Counted | " + " | ".join("methods" if c == "totalMethodsQty" else c for c in cols) + " |",
          "|---|---|" + "---:|" * len(cols)]
    for c in res["classes"]:
        b, a = c["before"] or {}, c["after"] or {}
        L.append(f"| {short(c['class'])} | {'yes' if c['counted'] else 'no'} | "
                 + " | ".join(_ba(b.get(k), a.get(k)) for k in cols) + " |")
    L += ["", "## Per method: target members and every new, removed or changed method (before → after)", "",
          "| Class | Method | Status | loc | CC (wmc) | params | cbo |", "|---|---|---|---:|---:|---:|---:|"]
    for x in res["methods"]:
        name, _, ptypes = _ck_method(x["method"])
        b, a = x["before"] or {}, x["after"] or {}
        L.append(f"| {short(x['class'])} | `{name}({', '.join(ptypes)})` | {x['status']} | "
                 + " | ".join(_ba(b.get(k), a.get(k)) for k in CK_METHOD_COLS) + " |")
    if not res["methods"]:
        L.append("| - | - | - | - | - | - | - |")
    L += ["", "## What the CK measures mean", "",
          "- **loc**: lines of code without blank lines and comments. **wmc**: for a class, the sum of the cyclomatic complexity (CC) of its methods; for a method, its CC.",
          "- **cbo**: number of other types a class (or method) depends on. **rfc**: number of distinct methods a class can invoke (response for a class).",
          "- **lcom**: CK's raw lack of cohesion of methods (pairs of methods sharing no field); it grows with the number of methods and CK itself calls it unreliable. "
          "**lcom\\***: Henderson-Sellers' normalised version, 0 = fully cohesive, 1 = no cohesion (lower is better). **tcc**: tight class cohesion, higher is better.",
          "- An Extract Method usually *adds* a little class loc (new signatures) and raises lcom/lcom\\* (more methods) even when the "
          "long method itself becomes much simpler; the per-method table shows that effect.", ""]
    return "\n".join(L)


def cmd_metrics(a):
    if a.all:
        todo = [(rd, m) for rd, m in all_runs() if m.get("status") == "finished" and m.get("commit")]
        if not todo:
            die("no finished runs to measure")
    else:
        if not (a.smell and a.llm):
            die("give --smell and --llm, or --all")
        rd, m = load_run(a.llm, a.smell)
        if m.get("status") != "finished" or not m.get("commit"):
            die(f"run {m['smell']} / {m['llm']} is not finished - run `python kit.py finish` first")
        todo = [(rd, m)]
    values = {}
    for rd, m in todo:
        print(f"[metrics] {m['smell']} / {m['llm']}")
        res = measure_run(rd, m)
        row = []
        for name in CFG.get("metrics", []):
            v = res["metrics"].get(name, {})
            row += [v.get("before"), v.get("after")]
        values[res["run"]] = row
        for name, v in res["metrics"].items():
            print(f"  {name:9} {_fmt(v['before']):>9} -> {_fmt(v['after']):>9}  ({_delta(v['before'], v['after'])})   {v['label']}, {v['aggregate']}")
        print(f"  details: {rel(rd / 'metrics.md')}")
    rebuild_log(set_metrics=values)


# ======================================================================================
# Excel log (always rebuilt from runs/, keeping what you typed in yellow cells)
# ======================================================================================
def all_runs():
    out = []
    for p in sorted((KIT / "runs").glob("*/*/run.json")):
        try:
            out.append((p.parent, json.loads(read(p))))
        except Exception:
            pass
    return out


def rebuild_log(set_metrics=None):
    """set_metrics: {run id: [m1 before, m1 after, m2 before, ...]} written by `kit.py metrics`; overrides that run's row."""
    try:
        from openpyxl import Workbook, load_workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.datavalidation import DataValidation  # noqa: F401
    except ImportError:
        die("openpyxl is missing: pip install openpyxl")

    path = KIT / CFG["log_workbook"]
    metrics = CFG.get("metrics", ["Size", "Cohesion", "Coupling"])
    keep_notes, keep_metrics = {}, {}
    if path.exists():
        try:
            old = load_workbook(path)
            if "Runs" in old.sheetnames:
                ws = old["Runs"]
                hdr = {str(c.value): c.column for c in ws[HDR] if c.value}
                if "Run ID" in hdr and "Your notes" in hdr:
                    for r in range(HDR + 1, ws.max_row + 1):
                        k = ws.cell(r, hdr["Run ID"]).value
                        if k:
                            keep_notes[k] = ws.cell(r, hdr["Your notes"]).value
            if "Metrics" in old.sheetnames:
                ws = old["Metrics"]
                for r in range(HDR + 1, ws.max_row + 1):
                    k = ws.cell(r, 1).value
                    if k:
                        keep_metrics[k] = [ws.cell(r, 4 + 3 * i + j).value for i in range(len(metrics)) for j in (0, 1)]
        except Exception as e:
            warn(f"could not read the existing log ({e}); notes and metric values may need re-entering")
    if set_metrics:
        keep_metrics.update(set_metrics)

    F = lambda **k: Font(name="Arial", size=k.pop("size", 10), **k)
    MONO = Font(name="Courier New", size=8)
    HEAD = PatternFill("solid", fgColor="1F3864")
    INPUT = PatternFill("solid", fgColor="FFF2CC")
    PASS = PatternFill("solid", fgColor="E2EFDA")
    REVIEW = PatternFill("solid", fgColor="FCE4D6")
    thin = Side(style="thin", color="BFBFBF")
    B = Border(left=thin, right=thin, top=thin, bottom=thin)
    WRAP = Alignment(wrap_text=True, vertical="top")
    CENTER = Alignment(horizontal="center", vertical="top", wrap_text=True)

    wb = Workbook()
    runs = all_runs()

    def title(ws, text, note):
        ws["A1"] = text
        ws["A1"].font = F(bold=True, size=13, color="1F3864")
        ws["A2"] = note
        ws["A2"].font = F(size=9, italic=True, color="404040")

    def header(ws, cols, user_from=None):
        for i, (name, width) in enumerate(cols, start=1):
            c = ws.cell(HDR, i, name)
            c.font = F(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="7F6000") if user_from and i >= user_from else HEAD
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = B
            ws.column_dimensions[get_column_letter(i)].width = width
        ws.row_dimensions[HDR].height = 32

    def clip(t):
        t = t or ""
        return t if len(t) <= EXCEL_CELL_LIMIT else t[:EXCEL_CELL_LIMIT] + "\n... [truncated - full code in the run folder]"

    # ---------------- Runs
    ws = wb.active
    ws.title = "Runs"
    title(ws, "Refactoring runs - Apache Commons CLI 1.9.0",
          "One row per smell x LLM. Rebuilt by kit.py from the runs/ folder after every start/finish; only the yellow column is yours and is kept between rebuilds.")
    cols = [("Run ID", 16), ("Smell ID", 8), ("Smell type", 12), ("Code smell", 16), ("Refactoring applied", 30), ("LLM", 12),
            ("Model / version", 16), ("Mode", 7), ("Status", 9), ("Started", 15), ("Finished", 15), ("Files changed", 30),
            ("Members changed", 9), ("Members new", 9), ("Members removed", 9), ("Lines added", 8), ("Lines removed", 8),
            ("Original code", 70), ("Refactored code", 70),
            ("Original tests passed", 10), ("Original tests total", 10), ("Refactored tests passed", 10), ("Refactored tests total", 10),
            ("Regressions", 10), ("Build OK", 8), ("Test files modified", 9), ("API removed / changed", 9), ("API added", 8),
            ("Verdict", 10), ("Run folder", 22), ("Key", 14), ("Your notes", 30)]
    header(ws, cols, user_from=len(cols))
    ci = {name: i for i, (name, _) in enumerate(cols, start=1)}
    for r, (rd, m) in enumerate(runs, start=HDR + 1):
        o = _load_json(rd / "tests_original.json")
        t = _load_json(rd / "tests_refactored.json")
        ch = _load_json(rd / "code_changes.json") or []
        rid = f"{m['smell']} - {m['llm']}"
        orig_code = code_blob(ch, "old") if ch else (read(rd / "original_smell_location.java.txt") if (rd / "original_smell_location.java.txt").exists() else "")
        mem = m.get("members", {})
        vals = {
            "Run ID": rid, "Smell ID": m["smell"], "Smell type": m["smell_type"], "Code smell": m["smell_name"],
            "Refactoring applied": m["technique"], "LLM": m["llm"], "Model / version": m["model"], "Mode": m["mode"],
            "Status": m["status"], "Started": m["started"], "Finished": m.get("finished", ""),
            "Files changed": "\n".join(m.get("files_changed", [])),
            "Members changed": mem.get("changed") if m["status"] == "finished" else None,
            "Members new": (mem.get("new", 0) + mem.get("new file", 0)) if m["status"] == "finished" else None,
            "Members removed": (mem.get("removed", 0) + mem.get("deleted file", 0)) if m["status"] == "finished" else None,
            "Lines added": m.get("lines_added"), "Lines removed": m.get("lines_removed"),
            "Original code": clip(orig_code), "Refactored code": clip(code_blob(ch, "new")) if ch else "",
            "Original tests passed": o["passed"] if o else None, "Original tests total": o["total"] if o else None,
            "Refactored tests passed": t["passed"] if t else None, "Refactored tests total": t["total"] if t else None,
            "Regressions": len(m.get("regressions", [])) if t else None,
            "Build OK": ("Yes" if t["build_ok"] else "No") if t else None,
            "Test files modified": ("Yes" if m.get("test_files_modified") else "No") if t else None,
            "API removed / changed": len(m.get("api_removed", [])) if t else None,
            "API added": len(m.get("api_added", [])) if t else None,
            "Run folder": rel(rd), "Your notes": keep_notes.get(rid),
        }
        for name, i in ci.items():
            c = ws.cell(r, i, vals.get(name))
            c.font = MONO if name in ("Original code", "Refactored code") else F()
            c.alignment = WRAP if name not in ("Members changed", "Members new", "Members removed", "Lines added", "Lines removed",
                                               "Original tests passed", "Original tests total", "Refactored tests passed",
                                               "Refactored tests total", "Regressions", "Build OK", "Test files modified",
                                               "API removed / changed", "API added", "Verdict", "Mode", "Smell ID") else CENTER
            c.border = B
        L = lambda n: f"{get_column_letter(ci[n])}{r}"
        ws.cell(r, ci["Verdict"], f'=IF({L("Status")}<>"finished","",IF(AND({L("Build OK")}="Yes",{L("Regressions")}=0,'
                                 f'{L("Test files modified")}="No",{L("API removed / changed")}=0,{L("Members changed")}+{L("Members new")}+{L("Members removed")}>0),"PASS","REVIEW"))')
        ws.cell(r, ci["Key"], f'={L("Smell ID")}&"|"&{L("LLM")}')
        ws.cell(r, ci["Your notes"]).fill = INPUT
        ws.cell(r, ci["Verdict"]).fill = PASS if m.get("verdict") == "PASS" else (REVIEW if m.get("verdict") else PatternFill())
        ws.cell(r, ci["Verdict"]).font = F(bold=True)
        ws.row_dimensions[r].height = 160
    ws.freeze_panes = ws.cell(HDR + 1, 3)
    if runs:
        ws.auto_filter.ref = f"A{HDR}:{get_column_letter(len(cols))}{HDR + len(runs)}"
    ws.column_dimensions[get_column_letter(ci["Key"])].hidden = True
    last = HDR + max(1, len(runs)) + 200

    # ---------------- Code Changes
    cc = wb.create_sheet("Code Changes")
    title(cc, "Code changes, member by member (original next to refactored)",
          "One row per changed, new or removed member. Line numbers refer to the original file (left) and the refactored file (right).")
    ccols = [("Run ID", 16), ("Smell ID", 8), ("LLM", 12), ("File", 22), ("Member", 34), ("Change", 10),
             ("Original lines", 10), ("Original code", 80), ("Refactored lines", 10), ("Refactored code", 80)]
    header(cc, ccols)
    r = HDR + 1
    for rd, m in runs:
        for c in _load_json(rd / "code_changes.json") or []:
            o, n = c["old"], c["new"]
            vals = [f"{m['smell']} - {m['llm']}", m["smell"], m["llm"], Path(c["file"]).name, c["member"], c["status"],
                    f"{o['start']}-{o['end']}" if o else "", clip(o["text"]) if o else "",
                    f"{n['start']}-{n['end']}" if n else "", clip(n["text"]) if n else ""]
            for i, v in enumerate(vals, start=1):
                cell = cc.cell(r, i, v)
                cell.font = MONO if i in (8, 10) else F()
                cell.alignment = WRAP
                cell.border = B
            lines = max((o["text"].count("\n") + 1) if o else 1, (n["text"].count("\n") + 1) if n else 1)
            cc.row_dimensions[r].height = min(400, 11 * lines + 6)
            r += 1
    cc.freeze_panes = cc.cell(HDR + 1, 6)
    if r > HDR + 1:
        cc.auto_filter.ref = f"A{HDR}:J{r - 1}"

    # ---------------- Comparison (smell x LLM)
    cp = wb.create_sheet("Comparison")
    title(cp, "Comparison: each smell across the LLMs",
          "Pulled from the Runs sheet with formulas. Verdict PASS = compiles, no regressions, tests untouched, no public/protected API removed.")
    llms = []
    for _, m in runs:
        if m["llm"] not in llms:
            llms.append(m["llm"])
    smells = []
    for _, m in runs:
        if m["smell"] not in smells:
            smells.append(m["smell"])
    smells.sort(key=lambda x: (x[0] != "W", x))
    metrics_per_llm = [("Verdict", "Verdict"), ("Refactored tests", None), ("Regressions", "Regressions"),
                       ("Lines +/-", None), ("Members chg/new/rem", None)]
    cp.column_dimensions["A"].width = 9
    cp.column_dimensions["B"].width = 18
    hc = 3
    for llm in llms:
        cp.cell(HDR - 1, hc, llm).font = F(bold=True, color="FFFFFF")
        cp.cell(HDR - 1, hc).fill = HEAD
        cp.cell(HDR - 1, hc).alignment = Alignment(horizontal="center")
        cp.merge_cells(start_row=HDR - 1, start_column=hc, end_row=HDR - 1, end_column=hc + len(metrics_per_llm) - 1)
        for j, (lab, _) in enumerate(metrics_per_llm):
            c = cp.cell(HDR, hc + j, lab)
            c.font = F(bold=True, color="FFFFFF", size=9)
            c.fill = HEAD
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = B
            cp.column_dimensions[get_column_letter(hc + j)].width = 12
        hc += len(metrics_per_llm)
    for j, lab in enumerate(("Smell ID", "Code smell")):
        c = cp.cell(HDR, 1 + j, lab)
        c.font = F(bold=True, color="FFFFFF")
        c.fill = HEAD
        c.border = B
    cp.row_dimensions[HDR].height = 30
    keycol = f"Runs!${get_column_letter(ci['Key'])}${HDR + 1}:${get_column_letter(ci['Key'])}${last}"

    def rcol(name):
        L_ = get_column_letter(ci[name])
        return f"Runs!${L_}${HDR + 1}:${L_}${last}"

    for r, sid in enumerate(smells, start=HDR + 1):
        name = next(m["smell_name"] for _, m in runs if m["smell"] == sid)
        cp.cell(r, 1, sid).font = F(bold=True)
        cp.cell(r, 2, name).font = F()
        hc = 3
        for llm in llms:
            kc = get_column_letter(hc)
            key = f'$A{r}&"|"&{kc}${HDR - 1}'
            m_ = f"MATCH({key},{keycol},0)"
            look = lambda n: f"INDEX({rcol(n)},{m_})"
            f = [f'=IFERROR({look("Verdict")},"-")',
                 f'=IFERROR(IF({look("Refactored tests total")}="","-",{look("Refactored tests passed")}&"/"&{look("Refactored tests total")}),"-")',
                 f'=IFERROR(IF({look("Regressions")}="","-",{look("Regressions")}),"-")',
                 f'=IFERROR(IF({look("Lines added")}="","-","+"&{look("Lines added")}&" / -"&{look("Lines removed")}),"-")',
                 f'=IFERROR(IF({look("Members changed")}="","-",{look("Members changed")}&"/"&{look("Members new")}&"/"&{look("Members removed")}),"-")']
            for j, formula in enumerate(f):
                c = cp.cell(r, hc + j, formula)
                c.font = F(bold=(j == 0))
                c.alignment = Alignment(horizontal="center")
                c.border = B
            # merged header cell holds the LLM name in the first column of the group
            hc += len(metrics_per_llm)
        for j in (1, 2):
            cp.cell(r, j).border = B
    cp.freeze_panes = cp.cell(HDR + 1, 3)

    # ---------------- Metrics (to fill)
    mt = wb.create_sheet("Metrics")
    title(mt, "Quality metrics before and after (filled by `python kit.py metrics` with CK; details in runs/<llm>/<ID>/metrics.md)",
          "Yellow cells are kept between rebuilds, so you may also type values; running `kit.py metrics` for a run overwrites that run's row. "
          "Change = After - Before. Metric names: config.json 'metrics'; CK columns and aggregation: config.json 'metric_tool'.")
    mcols = [("Run ID", 16), ("Smell ID", 8), ("LLM", 12)]
    for name in metrics:
        mcols += [(f"{name} before", 11), (f"{name} after", 11), (f"{name} change", 11)]
    header(mt, mcols)
    for r, (rd, m) in enumerate(runs, start=HDR + 1):
        rid = f"{m['smell']} - {m['llm']}"
        kept = keep_metrics.get(rid, [])
        for i, v in enumerate((rid, m["smell"], m["llm"]), start=1):
            mt.cell(r, i, v).font = F()
            mt.cell(r, i).border = B
        for k in range(len(metrics)):
            bcol, acol, dcol = 4 + 3 * k, 5 + 3 * k, 6 + 3 * k
            for j, cc_ in enumerate((bcol, acol)):
                v = kept[2 * k + j] if len(kept) > 2 * k + j else None
                c = mt.cell(r, cc_, v)
                c.fill = INPUT
                c.border = B
                c.font = F()
            bl, al = get_column_letter(bcol), get_column_letter(acol)
            c = mt.cell(r, dcol, f'=IF(OR({bl}{r}="",{al}{r}=""),"",{al}{r}-{bl}{r})')
            c.border = B
            c.font = F(bold=True)
    mt.freeze_panes = mt.cell(HDR + 1, 4)

    # ---------------- About
    ab = wb.create_sheet("About")
    lines = [
        ("Refactoring log - how it is filled", True),
        (f"Code base: {CFG['repo_url']} @ {CFG['tag']}", False),
        ("Runs: one row per smell x LLM. 'Original code' = every member the refactoring changed, as it was before "
         "(before finishing: the smell location). 'Refactored code' = the same members after, plus new ones.", False),
        ("Original tests = the project's own test suite run on the untouched code. Refactored tests = the same, unmodified "
         "suite run on the refactored code. Regressions = tests that passed before and do not pass after.", False),
        ("Verdict PASS = compiles, 0 regressions, no test file changed, no public/protected API removed or changed, and the code changed.", False),
        ("Code Changes: the same code, one row per member, original next to refactored.", False),
        ("Comparison: each smell across the LLMs (formulas over Runs).", False),
        ("Metrics: `python kit.py metrics --smell <ID> --llm <name>` (or `--all`) measures size / cohesion / coupling before and after with CK "
         "and fills the yellow cells; per-class and per-method details are in runs/<llm>/<ID>/metrics.md. You may still type your own values.", False),
        ("This file is rebuilt from runs/ by kit.py; edit only yellow cells. If Excel has it open, kit.py cannot save: close it and run `python kit.py log`.", False),
    ]
    for i, (t, bold) in enumerate(lines, start=1):
        c = ab.cell(i, 1, t)
        c.font = F(bold=bold, size=12 if bold else 10)
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ab.column_dimensions["A"].width = 120

    try:
        wb.calculation.fullCalcOnLoad = True
    except Exception:
        pass
    try:
        wb.save(path)
        print(f"  log updated: {CFG['log_workbook']} ({len(runs)} run(s))")
    except PermissionError:
        warn(f"could not write {CFG['log_workbook']} - is it open in Excel? Close it and run `python kit.py log`.")


HDR = 4  # header row in every log sheet


# ======================================================================================
def main():
    p = argparse.ArgumentParser(description="Refactoring starter kit (Apache Commons CLI 1.9.0)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="check that the required tools are installed")
    sp = sub.add_parser("show", help="print one smell from the review sheet")
    sp.add_argument("smell")
    sp = sub.add_parser("start", help="clone, save original code, run original tests, write the task")
    sp.add_argument("--smell", required=True)
    sp.add_argument("--llm", required=True, help="short LLM name, e.g. ChatGPT")
    sp.add_argument("--model", required=True, help="model name and version, e.g. 'GPT-5.1 (Nov 2026)'")
    sp.add_argument("--mode", choices=["agent", "chat"], default="agent")
    sp.add_argument("--base", help="start from this branch/commit instead of the tag (to stack refactorings)")
    sp.add_argument("--force", action="store_true", help="delete and restart an existing run")
    sp.add_argument("--fresh-baseline", action="store_true", help="re-run the original tests instead of using the cache")
    sp = sub.add_parser("test", help="run the tests in an LLM's workspace")
    sp.add_argument("--llm", required=True)
    sp.add_argument("--only", help="test class(es), e.g. HelpFormatterTest or 'HelpFormatterTest,OptionTest'")
    sp = sub.add_parser("apply", help="chat mode: write the files from the LLM reply into the workspace")
    sp.add_argument("--smell", required=True)
    sp.add_argument("--llm", required=True)
    sp.add_argument("--response", help="reply file (default: runs/<llm>/<smell>/response.md)")
    sp.add_argument("--force", action="store_true", help="write files even if they look truncated")
    sp = sub.add_parser("finish", help="test the refactored code, save everything, update the log")
    sp.add_argument("--smell", required=True)
    sp.add_argument("--llm", required=True)
    sp = sub.add_parser("metrics", help="measure size/cohesion/coupling before and after with CK and fill the Metrics sheet")
    sp.add_argument("--smell")
    sp.add_argument("--llm")
    sp.add_argument("--all", action="store_true", help="measure every finished run")
    sub.add_parser("log", help="rebuild Refactoring_Log.xlsx from runs/")
    sub.add_parser("status", help="list runs")
    a = p.parse_args()
    {"check": cmd_check, "show": cmd_show, "start": cmd_start, "test": cmd_test, "apply": cmd_apply,
     "finish": cmd_finish, "metrics": cmd_metrics, "log": cmd_log, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
