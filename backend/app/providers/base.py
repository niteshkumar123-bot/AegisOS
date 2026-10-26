from typing import Protocol
from pydantic import BaseModel

class PatchProposal(BaseModel):
    summary: str
    unified_diff: str
    rationale: str
    estimated_cost_usd: float = 0.0

class Provider(Protocol):
    name: str
    model: str
    def propose_patch(self, issue: str, context: str, language: str) -> PatchProposal: ...
    def review(self, issue: str, patch: str, test_evidence: dict) -> str: ...
