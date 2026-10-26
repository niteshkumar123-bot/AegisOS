from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db import get_db, SessionLocal
from app.models import User, Repository, Task, WorkflowEvent, AgentStep, TestResult, Evaluation, Experiment, ExperimentRun, AuditLog
from app.schemas import UserCreate, LoginRequest, TokenResponse, RepositoryCreate, RepositoryOut, TaskCreate, TaskOut, EventOut, ExperimentCreate, ExperimentOut
from app.security import hash_password,verify_password,create_token,current_user
from app.repositories.indexer import safe_workspace_path,index_repository
from app.workflow.engine import run_task,request_cancel
from app.config import get_settings
from datetime import datetime, timezone
import time
router=APIRouter(prefix="/api")

def audit(db,user,action,typ,rid): db.add(AuditLog(user_id=user.id if user else None,action=action,resource_type=typ,resource_id=str(rid))); db.commit()
def owned_task(db,task_id,user):
    t=db.get(Task,task_id)
    if not t or t.owner_id!=user.id: raise HTTPException(404,"Task not found")
    return t

@router.post("/auth/register",response_model=TokenResponse, status_code=201)
def register(body:UserCreate,db:Session=Depends(get_db)):
    email=body.email.lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,"Email is already registered")
    user=User(email=email,password_hash=hash_password(body.password)); db.add(user); db.commit(); db.refresh(user); audit(db,user,"register","user",user.id)
    return TokenResponse(access_token=create_token(user.id))
@router.post("/auth/login",response_model=TokenResponse)
def login(body:LoginRequest,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==body.email.lower()))
    if not user or not verify_password(body.password,user.password_hash): raise HTTPException(401,"Invalid email or password")
    return TokenResponse(access_token=create_token(user.id))
@router.get("/auth/me")
def me(user:User=Depends(current_user)): return {"id":user.id,"email":user.email}

@router.get("/repositories",response_model=list[RepositoryOut])
def list_repos(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return list(db.scalars(select(Repository).where(Repository.owner_id==user.id).order_by(Repository.id.desc()).limit(100)))
@router.post("/repositories",response_model=RepositoryOut,status_code=201)
def create_repo(body:RepositoryCreate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    try: path=safe_workspace_path(body.workspace_path,get_settings().workspace_path)
    except ValueError as e: raise HTTPException(422,str(e))
    if path.is_symlink(): raise HTTPException(422,"Symlink repository roots are not allowed")
    repo=Repository(owner_id=user.id,name=body.name,workspace_path=str(path),language=body.language); db.add(repo); db.commit(); db.refresh(repo); audit(db,user,"create","repository",repo.id); return repo
@router.get("/repositories/{repo_id}/index")
def index_repo(repo_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    repo=db.get(Repository,repo_id)
    if not repo or repo.owner_id!=user.id: raise HTTPException(404,"Repository not found")
    try: files=index_repository(safe_workspace_path(repo.workspace_path,get_settings().workspace_path))
    except ValueError as e: raise HTTPException(422,str(e))
    return {"repository_id":repo.id,"file_count":len(files),"files":[{"path":f["path"],"size":f["size"]} for f in files]}

@router.get("/tasks",response_model=list[TaskOut])
def list_tasks(db:Session=Depends(get_db),user:User=Depends(current_user),limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),status:str|None=None):
    q=select(Task).where(Task.owner_id==user.id)
    if status: q=q.where(Task.status==status)
    return list(db.scalars(q.order_by(Task.created_at.desc()).offset(offset).limit(limit)))
@router.post("/tasks",response_model=TaskOut,status_code=202)
def create_task(body:TaskCreate,bg:BackgroundTasks,db:Session=Depends(get_db),user:User=Depends(current_user)):
    if body.repository_id:
        repo=db.get(Repository,body.repository_id)
        if not repo or repo.owner_id!=user.id: raise HTTPException(404,"Repository not found")
    task=Task(owner_id=user.id,repository_id=body.repository_id,title=body.title,issue=body.issue,acceptance_criteria=body.acceptance_criteria,language=body.language,budget_usd=body.budget_usd,max_iterations=body.max_iterations,status="queued")
    db.add(task); db.commit(); db.refresh(task); db.add(WorkflowEvent(task_id=task.id,kind="state",status="queued",message="Task accepted and queued.")); db.commit(); audit(db,user,"create","task",task.id); bg.add_task(run_task,task.id,SessionLocal); return task
@router.get("/tasks/{task_id}",response_model=TaskOut)
def get_task(task_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)): return owned_task(db,task_id,user)
@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    task=owned_task(db,task_id,user)
    if task.status in {"completed","failed","cancelled"}: raise HTTPException(409,"Task is already terminal")
    task.cancelled=True; request_cancel(task_id); task.status="cancelled"; db.add(WorkflowEvent(task_id=task.id,kind="state",status="cancelled",message="Cancellation requested.")); db.commit(); return {"id":task.id,"status":"cancelled"}
@router.post("/tasks/{task_id}/rerun",response_model=TaskOut,status_code=202)
def rerun(task_id:int,bg:BackgroundTasks,db:Session=Depends(get_db),user:User=Depends(current_user)):
    old=owned_task(db,task_id,user); t=Task(owner_id=user.id,repository_id=old.repository_id,title=old.title+" (rerun)",issue=old.issue,acceptance_criteria=old.acceptance_criteria,language=old.language,budget_usd=old.budget_usd,max_iterations=old.max_iterations); db.add(t); db.commit(); db.refresh(t); db.add(WorkflowEvent(task_id=t.id,kind="state",status="queued",message=f"Rerun created from task {old.id}.",details={"retry_of":old.id})); db.commit(); bg.add_task(run_task,t.id,SessionLocal); return t
@router.get("/tasks/{task_id}/events",response_model=list[EventOut])
def events(task_id:int,db:Session=Depends(get_db),user:User=Depends(current_user),after_id:int=Query(0,ge=0)):
    owned_task(db,task_id,user); return list(db.scalars(select(WorkflowEvent).where(WorkflowEvent.task_id==task_id,WorkflowEvent.id>after_id).order_by(WorkflowEvent.id).limit(500)))
@router.get("/tasks/{task_id}/trace")
def trace(task_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    owned_task(db,task_id,user)
    return {"steps":[{"id":x.id,"role":x.role,"provider":x.provider,"model":x.model,"input_summary":x.input_summary,"output_summary":x.output_summary,"duration_ms":x.duration_ms,"error":x.error,"created_at":x.created_at} for x in db.scalars(select(AgentStep).where(AgentStep.task_id==task_id).order_by(AgentStep.id))],"tests":[{"id":x.id,"command":x.command,"exit_code":x.exit_code,"passed":x.passed,"duration_ms":x.duration_ms,"output":x.output,"evidence_kind":x.evidence_kind} for x in db.scalars(select(TestResult).where(TestResult.task_id==task_id).order_by(TestResult.id))],"evaluations":[{"verdict":x.verdict,"reasoning":x.reasoning,"evidence":x.evidence,"created_at":x.created_at} for x in db.scalars(select(Evaluation).where(Evaluation.task_id==task_id).order_by(Evaluation.id))]}

@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db),user:User=Depends(current_user)):
    tasks=list(db.scalars(select(Task).where(Task.owner_id==user.id).order_by(Task.created_at.desc()).limit(200)))
    done=[t for t in tasks if t.status=="completed"]
    success=sum(1 for t in done if t.verdict=="verified")
    return {"total_tasks":len(tasks),"active_tasks":sum(t.status not in {"completed","failed","cancelled"} for t in tasks),"completed_tasks":len(done),"failed_tasks":sum(t.status=="failed" or t.verdict=="failed" for t in tasks),"success_rate":round(success/len(done),4) if done else None,"avg_latency_ms":round(sum(t.latency_ms for t in done if t.latency_ms is not None)/sum(t.latency_ms is not None for t in done)) if any(t.latency_ms is not None for t in done) else None,"total_cost_usd":round(sum(t.cost_usd for t in tasks),6),"provider":get_settings().llm_provider,"sandbox_enabled":get_settings().sandbox_enabled,"recent_runs":[{"id":t.id,"title":t.title,"status":t.status,"verdict":t.verdict,"latency_ms":t.latency_ms,"created_at":t.created_at} for t in tasks[:10]]}

@router.post("/experiments",response_model=ExperimentOut,status_code=202)
def create_experiment(body:ExperimentCreate,bg:BackgroundTasks,db:Session=Depends(get_db),user:User=Depends(current_user)):
    exp=Experiment(owner_id=user.id,name=body.name,strategy_names=body.strategies,status="running"); db.add(exp); db.commit(); db.refresh(exp)
    # Execute actual provider calls and measure wall time. No test pass is inferred here:
    # without sandbox-backed checks, each sample must remain inconclusive.
    from app.providers import get_provider
    from app.evaluation.evaluator import validate_unified_diff
    try:
        provider=get_provider()
        for i,description in enumerate(body.task_descriptions):
            for strategy in body.strategies:
                started=time.monotonic(); cost=0.0; proposal=None; error=None
                try:
                    context="Experiment context is supplied by the task description only; no repository is attached."
                    attempts=2 if strategy=="iterative" else 1
                    for _ in range(attempts):
                        proposal=provider.propose_patch(description,context,"text")
                        valid,_=validate_unified_diff(proposal.unified_diff)
                        cost += proposal.estimated_cost_usd
                        if valid: break
                    if strategy=="multi_agent" and proposal is not None:
                        provider.review(description,proposal.unified_diff,{"execution":"not run","reason":"experiment harness does not execute code"})
                except Exception as exc:
                    error=type(exc).__name__
                latency=max(1,int((time.monotonic()-started)*1000))
                db.add(ExperimentRun(experiment_id=exp.id,strategy=strategy,sample_index=i,status="completed" if error is None else "failed",verdict="inconclusive" if error is None else "failed",cost_usd=max(0.0,cost),latency_ms=latency,first_attempt_success=False,regression=False,is_demo=(provider.name=="mock")))
        exp.status="completed"
    except Exception:
        exp.status="failed"
    db.commit(); db.refresh(exp); return exp
@router.get("/experiments",response_model=list[ExperimentOut])
def list_experiments(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return list(db.scalars(select(Experiment).where(Experiment.owner_id==user.id).order_by(Experiment.id.desc()).limit(100)))
@router.get("/experiments/{exp_id}")
def experiment_detail(exp_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    exp=db.get(Experiment,exp_id)
    if not exp or exp.owner_id!=user.id: raise HTTPException(404,"Experiment not found")
    runs=list(db.scalars(select(ExperimentRun).where(ExperimentRun.experiment_id==exp.id)))
    metrics=[]
    for strategy in exp.strategy_names:
        group=[r for r in runs if r.strategy==strategy]; n=len(group); verified=sum(r.verdict=="verified" for r in group)
        metrics.append({"strategy":strategy,"samples":n,"pass_rate":verified/n if n else None,"first_attempt_success_rate":sum(r.first_attempt_success for r in group)/n if n else None,"regression_rate":sum(r.regression for r in group)/n if n else None,"mean_cost_usd":sum(r.cost_usd for r in group)/n if n else None,"mean_latency_ms":sum(r.latency_ms for r in group)/n if n else None,"demo_data":any(r.is_demo for r in group)})
    return {"id":exp.id,"name":exp.name,"status":exp.status,"metrics":metrics,"runs":[{"strategy":r.strategy,"sample_index":r.sample_index,"verdict":r.verdict,"latency_ms":r.latency_ms,"is_demo":r.is_demo} for r in runs]}
@router.get("/metrics")
def metrics(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return {"task_count":db.scalar(select(func.count()).select_from(Task).where(Task.owner_id==user.id)) or 0,"event_count":db.scalar(select(func.count()).select_from(WorkflowEvent).join(Task).where(Task.owner_id==user.id)) or 0}
