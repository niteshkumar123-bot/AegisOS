from app.providers.mock import MockProvider
from app.evaluation.evaluator import validate_unified_diff
from app.sandbox.runner import apply_unified_diff


def test_division_by_zero_mock_patch_matches_real_context():
    source = (
        'def divide(a, b):\n'
        '    if b == 0:\n'
        '        raise ValueError("division by zero")\n'
        '    return a / b\n'
    )
    proposal = MockProvider().propose_patch(
        "Handle division by zero clearly",
        f"FILE: calculator.py\n{source}\n",
        "python",
    )
    valid, message = validate_unified_diff(proposal.unified_diff)
    assert valid, message
    patched = apply_unified_diff([{"path": "calculator.py", "text": source, "size": len(source)}], proposal.unified_diff)
    assert 'ValueError("cannot divide by zero")' in patched[0]["text"]
    assert "return a / b" in patched[0]["text"]


def test_mock_provider_handles_generic_division_issue():
    source = (
        'def divide(a, b):\n'
        '    if b == 0:\n'
        '        raise ValueError("division by zero")\n'
        '    return a / b\n'
    )
    proposal = MockProvider().propose_patch(
        "Review division behavior and propose a safer edge-case handling change.",
        f"FILE: calculator.py\n{source}\n",
        "python",
    )
    assert proposal.unified_diff, "Generic division issue should produce a deterministic patch"
    valid, message = validate_unified_diff(proposal.unified_diff)
    assert valid, message
    assert 'cannot divide by zero' in proposal.unified_diff


def test_mock_provider_does_not_fabricate_patch_for_unsupported_task():
    source = "def greet(name):\n    return f'Hello {name}'\n"
    proposal = MockProvider().propose_patch(
        "Add a caching layer",
        f"FILE: greeting.py\n{source}\n",
        "python",
    )
    assert proposal.unified_diff == ""
    valid, _ = validate_unified_diff(proposal.unified_diff)
    assert not valid
