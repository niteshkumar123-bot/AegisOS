def evaluate(test_evidence: dict, acceptance_criteria: list[str], patch_valid: bool) -> tuple[str,str,dict]:
    evidence={"tests":test_evidence,"acceptance_criteria":acceptance_criteria,"patch_valid":patch_valid}
    if not patch_valid:
        return "failed","Patch validation failed; the proposed change was rejected before execution.",evidence
    if not test_evidence.get("available"):
        return "inconclusive",test_evidence.get("reason","No independent execution evidence is available."),evidence
    if test_evidence.get("exit_code") not in (None,0):
        return "failed","An executed independent check failed. The patch is not verified.",evidence
    if test_evidence.get("exit_code") is None:
        return "inconclusive",test_evidence.get("reason","No independent execution evidence is available."),evidence
    if not test_evidence.get("tests_executed",False):
        return "inconclusive","The execution result did not include independent project tests or acceptance evidence; the patch is not verified.",evidence
    if not test_evidence.get("acceptance_checks_passed",False):
        return "inconclusive","The available compile check passed, but acceptance criteria and project tests were not independently demonstrated.",evidence
    return "verified","All configured independent checks and acceptance checks passed.",evidence

def validate_unified_diff(diff: str) -> tuple[bool,str]:
    if not diff or len(diff)>500_000: return False,"Patch is empty or exceeds 500 KB."
    lines=diff.splitlines()
    paths=[]
    for line in lines:
        if line.startswith(("--- ","+++ ")):
            p=line[4:].split("\t",1)[0]
            if p in ("/dev/null",): continue
            if p.startswith(("a/","b/")): p=p[2:]
            from pathlib import PurePosixPath
            path=PurePosixPath(p)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                return False,"Patch contains an unsafe path."
            if ":" in path.parts[0] or "\\" in p: return False,"Patch contains an invalid path."
            paths.append(p)
    if not paths: return False,"Patch contains no file headers."
    if not any(x.startswith("@@ ") for x in lines): return False,"Patch contains no unified-diff hunk."
    return True,"Patch path and structure checks passed."
