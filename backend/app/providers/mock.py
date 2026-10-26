"""Deterministic, context-matched demo patch provider.

The mock provider intentionally supports a small, explicit transformation set.
It never fabricates a placeholder diff against text that is not in the repository.
Unsupported requests return an empty patch; normal patch validation then rejects it.
"""
from __future__ import annotations

import difflib
import re

from app.providers.base import PatchProposal


def _first_file(context: str) -> tuple[str, str] | None:
    """Extract the first FILE: block emitted by the repository context retriever."""
    current_path: str | None = None
    collected: list[str] = []
    files: list[tuple[str, str]] = []
    for line in context.splitlines(keepends=True):
        if line.startswith("FILE: "):
            if current_path is not None:
                files.append((current_path, "".join(collected)))
            current_path = line[6:].strip()
            collected = []
        elif current_path is not None:
            collected.append(line)
    if current_path is not None:
        files.append((current_path, "".join(collected)))
    if not files:
        return None
    # Prefer an actual function implementation over test files when the issue
    # concerns a known deterministic demo transformation.
    path, source = next(
        ((path, source) for path, source in files if re.search(r"^\s*def\s+divide\s*\(", source, re.M)),
        files[0],
    )
    # retrieve_context adds one delimiter newline after each file. Remove that
    # one synthetic newline so diff hunk counts and context match actual bytes.
    if source.endswith("\n"):
        source = source[:-1]
    return path, source


def _make_diff(path: str, original: str, updated: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
    )


class MockProvider:
    name = "mock"
    model = "deterministic-v1"

    def propose_patch(self, issue: str, context: str, language: str) -> PatchProposal:
        entry = _first_file(context)
        if not entry:
            return PatchProposal(
                summary="No repository file context was available for a safe demo patch",
                unified_diff="",
                rationale="The deterministic mock refuses to invent a file or pretend a patch is applicable.",
                estimated_cost_usd=0.0,
            )
        path, source = entry
        issue_lower = issue.lower()
        updated = source
        summary = "No supported deterministic transformation matched this task"
        rationale = "The mock provider supports only explicit demo transformations; no patch was fabricated."

        # Seed-task demo: replace a vague message with a clearer one while retaining
        # the existing exception class and normal division behavior.
        if (
            language.lower() == "python"
            and (
                any(term in issue_lower for term in ("division by zero", "divide by zero", "division zero", "edge-case handling change", "review division behavior"))
                or "division" in issue_lower and "behavior" in issue_lower
            )
            and re.search(r"raise\s+ValueError\([\"']division by zero[\"']\)", source)
        ):
            updated = re.sub(
                r"(raise\s+ValueError\()([\"'])division by zero([\"']\))",
                r"\1\2cannot divide by zero\3",
                source,
                count=1,
            )
            if updated != source:
                summary = "Clarified the division-by-zero error message in the existing implementation"
                rationale = "The patch is derived from the retrieved calculator.py contents and preserves the existing ValueError behavior. It still requires independent tests."

        diff = _make_diff(path, source, updated) if updated != source else ""
        return PatchProposal(
            summary=summary,
            unified_diff=diff,
            rationale=rationale,
            estimated_cost_usd=0.0,
        )

    def review(self, issue: str, patch: str, test_evidence: dict) -> str:
        return "Mock review is advisory only. Correctness verdict depends on independent execution evidence and acceptance checks."
