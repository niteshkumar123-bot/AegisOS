import time, threading
from sqlalchemy.orm import Session
from app.models import Task, WorkflowEvent, AgentStep, TestResult, Evaluation
from app.providers import get_provider
from app.repositories.indexer import safe_workspace_path,index_repository,retrieve_context
from app.sandbox.runner import run_python_tests
from app.evaluation.evaluator import evaluate,validate_unified_diff
from app.config import get_settings

TERMINAL={"completed","failed","cancelled"}
_cancel: dict[int, threading.Event]={}

def request_cancel(task_id: int): _cancel.setdefault(task_id,threading.Event()).set()
def _event(db, task, status, message, kind="state", details=None):
    task.status=status; db.add(WorkflowEvent(task_id=task.id,kind=kind,status=status,message=message,details=details or {})); db.commit()
def _step(db,task,role,provider,inp,out,ms,error=None):
    db.add(AgentStep(task_id=task.id,role=role,provider=provider.name,model=provider.model,input_summary=inp[:1000],output_summary=out[:3000],duration_ms=ms,error=error)); db.commit()
def run_task(task_id: int, factory):
    db=factory(); start=time.monotonic(); task=db.get(Task,task_id)
    if not task: db.close(); return
    if task.status not in ("queued",): db.close(); return
    _cancel[task_id]=threading.Event()
    try:
        _event(db,task,"analyzing","Starting repository analysis.")
        if _cancel[task_id].is_set(): task.status="cancelled"; db.commit(); return
        context="No repository attached. Patch proposal will be treated as unverified."
        files=[]
        if task.repository_id:
            from app.models import Repository
            repo=db.get(Repository,task.repository_id)
            if not repo or repo.owner_id != task.owner_id: raise ValueError("Repository is unavailable")
            root=safe_workspace_path(repo.workspace_path,get_settings().workspace_path)
            files=index_repository(root); context=retrieve_context(files,task.issue)
        provider=get_provider()
        t=time.monotonic(); _event(db,task,"planning","Planner is creating a bounded change plan.","agent",{"role":"planner"})
        plan="Identify the smallest change; preserve existing behavior; require independent checks."
        _step(db,task,"planner",provider,task.issue,plan,int((time.monotonic()-t)*1000))
        if _cancel[task_id].is_set(): task.status="cancelled"; db.commit(); return
        _event(db,task,"generating","Developer role is proposing a patch.")
        proposal=None; valid=False; validation="No proposal generated."; total_estimated_cost=0.0
        for attempt in range(task.max_iterations):
            if _cancel[task_id].is_set(): task.status="cancelled"; db.commit(); return
            t=time.monotonic(); proposal=provider.propose_patch(task.issue,context,task.language)
            total_estimated_cost += max(0.0,proposal.estimated_cost_usd)
            valid,validation=validate_unified_diff(proposal.unified_diff)
            _step(db,task,"developer",provider,f"Attempt {attempt+1}/{task.max_iterations}: {task.issue}",proposal.summary+"\n"+validation,int((time.monotonic()-t)*1000))
            if valid: break
        if proposal is None: raise RuntimeError("Provider returned no patch proposal")
        task.patch=proposal.unified_diff; task.cost_usd=min(task.budget_usd,total_estimated_cost)
        _step(db,task,"reviewer",provider,proposal.unified_diff,provider.review(task.issue,proposal.unified_diff,{"executed":False}),0)
        if _cancel[task_id].is_set(): task.status="cancelled"; db.commit(); return
        _event(db,task,"testing","Running isolated checks only if sandbox is enabled.")
        ev=run_python_tests(files,proposal.unified_diff) if files and valid else None
        if _cancel[task_id].is_set():
            task.status="cancelled"; db.add(WorkflowEvent(task_id=task.id,kind="state",status="cancelled",message="Task cancelled before evaluation.")); db.commit(); return
        testdata={
            "available": bool(ev and ev.available),
            "exit_code": ev.exit_code if ev else None,
            "output": ev.output if ev else "",
            "duration_ms": ev.duration_ms if ev else 0,
            "reason": ev.reason if ev else ("No repository files were available to execute." if not files else validation),
            "tests_executed": bool(ev and ev.tests_executed),
            "acceptance_tests_executed": bool(ev and ev.acceptance_tests_executed),
            "acceptance_checks_passed": bool(ev and ev.acceptance_tests_executed and ev.exit_code == 0),
        }
        command = (
            "Python AST + unittest acceptance checks (sandbox gated)"
            if testdata["tests_executed"]
            else "Python AST syntax validation (sandbox gated)"
        )
        db.add(TestResult(task_id=task.id,command=command,exit_code=testdata["exit_code"],passed=(testdata["exit_code"]==0 if testdata["exit_code"] is not None else None),duration_ms=testdata["duration_ms"],output=testdata["output"] or testdata["reason"],evidence_kind="sandbox" if testdata["available"] else "unavailable")); db.commit()
        _event(db,task,"evaluating","Evaluator is checking collected evidence.")
        verdict,reason,evidence=evaluate(testdata,task.acceptance_criteria,valid)
        db.add(Evaluation(task_id=task.id,verdict=verdict,reasoning=reason,evidence=evidence)); task.verdict=verdict
        task.status="completed" if verdict in ("verified","failed","inconclusive") else "failed"
        task.latency_ms=int((time.monotonic()-start)*1000); task.updated_at=task.updated_at
        db.add(WorkflowEvent(task_id=task.id,kind="evaluation",status=task.status,message=reason,details={"verdict":verdict,"validation":validation})); db.commit()
    except Exception as e:
        db.rollback(); task=db.get(Task,task_id)
        if task:
            task.status="failed"; task.verdict="inconclusive"; task.error_message=f"Workflow failed safely: {type(e).__name__}"; task.latency_ms=int((time.monotonic()-start)*1000)
            db.add(WorkflowEvent(task_id=task.id,kind="error",status="failed",message="Workflow failed; details are redacted from client response.",details={"error_type":type(e).__name__})); db.commit()
    finally:
        _cancel.pop(task_id,None); db.close()
