import re
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Literal, Any

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
class LoginRequest(BaseModel):
    # Login identifiers may be local development addresses such as demo@aegisos.local.
    # Account registration remains strict EmailStr validation in UserCreate.
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_login_email(cls, value: str) -> str:
        value = value.strip().lower()
        if value.endswith(".local"):
            # EmailStr intentionally rejects special-use domains; permit .local only
            # for login lookup so existing local demo accounts remain usable.
            pattern = r"^[^@\s]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.local$"
            if not re.fullmatch(pattern, value) or ".." in value:
                raise ValueError("Enter a valid email address")
            return value
        try:
            return validate_email(value, check_deliverability=False).normalized.lower()
        except EmailNotValidError as exc:
            raise ValueError("Enter a valid email address") from exc
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    workspace_path: str = Field(min_length=1, max_length=1024)
    language: str = Field(default="unknown", max_length=40)
class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; workspace_path: str; language: str
class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    issue: str = Field(min_length=10, max_length=12000)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=30)
    language: str = Field(default="python", max_length=40)
    repository_id: int | None = None
    budget_usd: float = Field(default=0.25, ge=0, le=25)
    max_iterations: int = Field(default=2, ge=1, le=5)
class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; title: str; issue: str; acceptance_criteria: list[str]; language: str
    status: str; verdict: str | None; patch: str | None; error_message: str | None
    budget_usd: float; cost_usd: float; latency_ms: int | None; created_at: Any
class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; kind: str; status: str; message: str; details: dict; created_at: Any
class ExperimentCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    task_descriptions: list[str] = Field(min_length=1, max_length=20)
    strategies: list[Literal["baseline", "iterative", "multi_agent"]] = Field(default_factory=lambda: ["baseline", "iterative", "multi_agent"], min_length=1, max_length=3)
class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; strategy_names: list; status: str; created_at: Any
