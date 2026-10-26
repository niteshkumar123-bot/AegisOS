from pathlib import Path

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import Repository, Task, User, WorkflowEvent
from app.security import hash_password, verify_password

DEMO_EMAIL = "demo@aegisos.dev"
LEGACY_DEMO_EMAIL = "demo@aegisos.local"
DEMO_PASSWORD = "AegisOS-demo-password-2026"

settings = get_settings()
root = settings.workspace_path / "demo-repository"
root.mkdir(parents=True, exist_ok=True)
(root / "calculator.py").write_text(
    'def divide(a, b):\n    if b == 0:\n        raise ValueError("division by zero")\n    return a / b\n',
    encoding="utf-8",
)
Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    user = db.query(User).filter_by(email=DEMO_EMAIL).first()
    legacy_user = db.query(User).filter_by(email=LEGACY_DEMO_EMAIL).first()

    if user is None and legacy_user is not None:
        # Preserve existing repository/task ownership when upgrading an old demo DB.
        legacy_user.email = DEMO_EMAIL
        user = legacy_user
        db.commit()
        db.refresh(user)
    elif user is None:
        user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.commit()
        db.refresh(user)

    # This script is for local development: keep the documented demo password usable.
    if not verify_password(DEMO_PASSWORD, user.password_hash):
        user.password_hash = hash_password(DEMO_PASSWORD)
        db.commit()

    repo = db.query(Repository).filter_by(owner_id=user.id, name="Demo Python Repository").first()
    if repo is None:
        repo = Repository(
            owner_id=user.id,
            name="Demo Python Repository",
            workspace_path=str(root.resolve()),
            language="python",
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

    task = db.query(Task).filter_by(
        owner_id=user.id, title="Handle division by zero clearly"
    ).first()
    if task is None:
        task = Task(
            owner_id=user.id,
            repository_id=repo.id,
            title="Handle division by zero clearly",
            issue="Review division behavior and propose a safer edge-case handling change.",
            acceptance_criteria=[
                "Division by zero behavior is explicit",
                "Existing valid division still works",
            ],
            language="python",
            status="queued",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        db.add(WorkflowEvent(
            task_id=task.id,
            kind="seed",
            status="queued",
            message="Seed task ready to run.",
        ))
        db.commit()

    print(f"Seed complete. Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
finally:
    db.close()
