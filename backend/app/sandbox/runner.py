from dataclasses import dataclass
import subprocess, tempfile, shutil, time, textwrap
from pathlib import Path
from app.config import get_settings

@dataclass
class RunEvidence:
    available: bool
    exit_code: int | None
    output: str
    duration_ms: int
    reason: str = ""
    tests_executed: bool = False
    acceptance_tests_executed: bool = False

def apply_unified_diff(source_files: list[dict], diff: str) -> list[dict]:
    """Apply a strict subset of unified diffs to an isolated in-memory copy.

    Only existing indexed files and context-matching hunks are accepted. File creation,
    deletion, binary patches, renames, and fuzzy application are rejected explicitly.
    """
    import re
    by_path={item["path"]:dict(item) for item in source_files}
    lines=diff.splitlines(keepends=True); i=0
    while i < len(lines):
        if not lines[i].startswith("--- "):
            i+=1; continue
        old_path=lines[i][4:].strip().split("\t",1)[0]; i+=1
        if i>=len(lines) or not lines[i].startswith("+++ "): raise ValueError("Malformed unified diff file headers")
        new_path=lines[i][4:].strip().split("\t",1)[0]; i+=1
        if old_path=="/dev/null" or new_path=="/dev/null" or old_path[2:]!=new_path[2:]:
            raise ValueError("File creation, deletion, and rename patches are not supported by this runner")
        path=new_path[2:] if new_path.startswith("b/") else new_path
        if path not in by_path: raise ValueError("Patch target is not an indexed existing file")
        original=by_path[path]["text"].splitlines(keepends=True); output=[]; cursor=0
        while i<len(lines) and lines[i].startswith("@@ "):
            m=re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",lines[i])
            if not m: raise ValueError("Malformed unified diff hunk header")
            old_start=int(m.group(1)); i+=1; target=max(0,old_start-1)
            if target<cursor or target>len(original): raise ValueError("Patch hunk is out of range")
            output.extend(original[cursor:target]); cursor=target
            while i<len(lines) and not lines[i].startswith(("@@ ","--- ")):
                line=lines[i]
                if line.startswith("\\ No newline at end of file"):
                    i+=1; continue
                if not line or line[0] not in " +-": raise ValueError("Unsupported unified diff line")
                body=line[1:]
                if line[0] in " -":
                    if cursor>=len(original) or original[cursor].rstrip("\r\n")!=body.rstrip("\r\n"):
                        raise ValueError("Patch context does not match repository content")
                    if line[0]==" ": output.append(original[cursor])
                    cursor+=1
                if line[0]=="+": output.append(body)
                i+=1
            # hunk ended at next hunk or next file header; outer loop handles it.
        output.extend(original[cursor:]); by_path[path]["text"]="".join(output)
    if not any(item["text"] != next((x["text"] for x in source_files if x["path"]==item["path"]),None) for item in by_path.values()):
        raise ValueError("Patch did not change any indexed file")
    return list(by_path.values())

def run_python_tests(source_files: list[dict], patch: str) -> RunEvidence:
    s=get_settings()
    if not s.sandbox_enabled: return RunEvidence(False,None,"",0,"Sandbox disabled by configuration; uploaded code was not executed.")
    if not shutil.which("docker"): return RunEvidence(False,None,"",0,"Docker executable unavailable; sandbox execution refused.")
    start=time.monotonic()
    try:
        patched_files=apply_unified_diff(source_files,patch)
    except ValueError as e:
        return RunEvidence(True,2,str(e),int((time.monotonic()-start)*1000),"Patch could not be applied safely to the disposable workspace.")
    with tempfile.TemporaryDirectory(prefix="aegisos-job-") as td:
        root=Path(td).resolve()
        for item in patched_files:
            rel=Path(item["path"])
            if rel.is_absolute() or ".." in rel.parts: return RunEvidence(False,None,"",0,"Unsafe file path rejected.")
            dest=(root/rel).resolve()
            if root not in dest.parents and dest != root: return RunEvidence(False,None,"",0,"Unsafe file path rejected.")
            dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(item["text"],encoding="utf-8")
        # Test code is repository-controlled and therefore untrusted. It is only run
        # inside this disposable, network-disabled, resource-limited container.
        test_files = [
            item["path"] for item in patched_files
            if Path(item["path"]).name.startswith("test_") or Path(item["path"]).name.endswith("_test.py")
        ]
        has_acceptance_tests = any(Path(path).name == "test_aegis_acceptance.py" for path in test_files)
        sandbox_script = textwrap.dedent(
            """
            import ast, pathlib, sys, unittest
            root = pathlib.Path('.')
            files = sorted(p for p in root.rglob('*.py') if p.is_file())
            for path in files:
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            print(f'Parsed {len(files)} Python files')
            has_acceptance = pathlib.Path('test_aegis_acceptance.py').is_file()
            print(f'ACCEPTANCE_TEST_FILE_PRESENT={has_acceptance}')
            suite = unittest.defaultTestLoader.discover('.', pattern='test_*.py')
            count = suite.countTestCases()
            if count == 0:
                print('No unittest tests discovered; syntax validation only.')
                sys.exit(0)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            print(f'UNITTESTS_EXECUTED={result.testsRun}')
            print(f'UNITTESTS_FAILURES={len(result.failures) + len(result.errors)}')
            sys.exit(0 if result.wasSuccessful() else 1)
            """
        )
        cmd=[
            "docker", "run", "--rm", "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=64",
            "--memory", s.sandbox_memory, "--cpus", str(s.sandbox_cpus),
            "--user", "65534:65534", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
            "--mount", f"type=bind,src={root},dst=/workspace,readonly",
            "-w", "/workspace", s.sandbox_image, "python", "-c", sandbox_script
        ]
        try:
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=s.sandbox_timeout_seconds,check=False)
            output=(result.stdout+"\n"+result.stderr)[-12000:]
            # Avoid persisting source excerpts that a compiler/test failure may echo.
            for item in patched_files:
                for source_line in item["text"].splitlines():
                    if source_line.strip(): output=output.replace(source_line,"[source line redacted]")
            executed = "UNITTESTS_EXECUTED=" in output
            acceptance_executed = has_acceptance_tests and "ACCEPTANCE_TEST_FILE_PRESENT=True" in output and executed
            if acceptance_executed:
                reason = "Explicit AegisOS acceptance tests executed in the isolated container."
            elif executed:
                reason = "Repository unit tests executed, but no AegisOS acceptance-test marker was present."
            else:
                reason = "AST syntax validation completed; no runnable unittest tests were discovered."
            return RunEvidence(
                True, result.returncode, output, int((time.monotonic()-start)*1000), reason,
                tests_executed=executed, acceptance_tests_executed=acceptance_executed
            )
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
            return RunEvidence(True,124,(stdout+stderr)[-12000:],int((time.monotonic()-start)*1000),"Sandbox execution timed out.")
        except OSError:
            return RunEvidence(False,None,"",int((time.monotonic()-start)*1000),"Docker execution failed before a result was collected.")
