from app.evaluation.evaluator import evaluate,validate_unified_diff

def test_missing_sandbox_is_inconclusive():
    verdict,reason,_=evaluate({"available":False,"reason":"sandbox disabled"},["works"],True)
    assert verdict=="inconclusive" and "disabled" in reason
def test_failed_check_fails():
    verdict,_,_=evaluate({"available":True,"exit_code":1},[],True)
    assert verdict=="failed"
def test_compile_only_is_not_verified():
    verdict,_,_=evaluate({"available":True,"exit_code":0,"acceptance_checks_passed":False},["works"],True)
    assert verdict=="inconclusive"

def test_missing_execution_evidence_is_inconclusive():
    verdict, reason, _ = evaluate({"available": True, "exit_code": None, "reason": "No independent execution evidence is available."}, ["works"], True)
    assert verdict == "inconclusive" and "evidence" in reason.lower()


def test_verified_requires_real_execution_evidence():
    verdict, _, _ = evaluate({"available": True, "exit_code": 0, "tests_executed": True, "acceptance_checks_passed": True}, ["works"], True)
    assert verdict == "verified"


def test_patch_path_traversal_rejected():
    ok,_=validate_unified_diff("--- a/../../etc/passwd\n+++ b/../../etc/passwd\n@@ -1 +1 @@\n-a\n+b")
    assert not ok
def test_valid_diff_structure():
    ok,_=validate_unified_diff("--- a/src.py\n+++ b/src.py\n@@ -1 +1 @@\n-a\n+b")
    assert ok


def test_patch_rejects_windows_absolute_path():
    ok,_=validate_unified_diff("--- a/C:\\Windows\\system.ini\n+++ b/C:\\Windows\\system.ini\n@@ -1 +1 @@\n-a\n+b")
    assert not ok

def test_apply_patch_requires_matching_context():
    from app.sandbox.runner import apply_unified_diff
    files=[{"path":"app.py","text":"def value():\n    return 1\n","size":26}]
    diff="--- a/app.py\n+++ b/app.py\n@@ -2,1 +2,1 @@\n-    return 1\n+    return 2\n"
    patched=apply_unified_diff(files,diff)
    assert "return 2" in patched[0]["text"]

def test_apply_patch_rejects_fuzzy_context():
    from app.sandbox.runner import apply_unified_diff
    files=[{"path":"app.py","text":"def value():\n    return 1\n","size":26}]
    diff="--- a/app.py\n+++ b/app.py\n@@ -2,1 +2,1 @@\n-    return 9\n+    return 2\n"
    import pytest
    with pytest.raises(ValueError):
        apply_unified_diff(files,diff)
