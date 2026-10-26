import logging, time, threading
from collections import defaultdict, deque
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import get_settings
from app.db import engine
from app import models
from app.api.routes import router

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s %(message)s")
log=logging.getLogger("aegisos")
s=get_settings()
_rate_lock=threading.Lock()
_rate_buckets=defaultdict(deque)
app=FastAPI(title="AegisOS API",version="0.1.0",description="Evidence-driven AI software change platform",docs_url="/docs",redoc_url="/redoc")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in s.cors_origins.split(",") if x.strip()],allow_credentials=True,allow_methods=["GET","POST","OPTIONS"],allow_headers=["Authorization","Content-Type","X-Request-ID"])
@app.middleware("http")
async def rate_limit(request:Request,call_next):
    # Process-local sliding window. Deployments with multiple replicas should enforce
    # shared limits at the gateway or use Redis; do not trust arbitrary X-Forwarded-For.
    if request.url.path.startswith("/api/"):
        client=request.client.host if request.client else "unknown"
        key=(client,request.url.path.split("/",3)[2] if len(request.url.path.split("/",3))>2 else "api")
        now=time.monotonic()
        with _rate_lock:
            bucket=_rate_buckets[key]
            while bucket and now-bucket[0]>60: bucket.popleft()
            if len(bucket)>=s.rate_limit_per_minute:
                return JSONResponse(status_code=429,content={"detail":"Rate limit exceeded; retry shortly."},headers={"Retry-After":"60"})
            bucket.append(now)
    return await call_next(request)
@app.middleware("http")
async def request_logging(request:Request,call_next):
    started=time.monotonic(); response=None
    try:
        response=await call_next(request); return response
    finally:
        log.info("request method=%s path=%s status=%s duration_ms=%d",request.method,request.url.path,getattr(response,"status_code",500),int((time.monotonic()-started)*1000))
@app.exception_handler(Exception)
async def safe_error(request:Request,exc:Exception):
    log.exception("unhandled error type=%s",type(exc).__name__)
    return JSONResponse(status_code=500,content={"detail":"Internal server error","request_id":request.headers.get("x-request-id")})
@app.get("/health")
def health(): return {"status":"ok","service":"aegisos-api"}
@app.get("/ready")
def ready():
    try:
        with engine.connect() as c: c.execute(text("SELECT 1"))
        return {"status":"ready","database":"ok"}
    except Exception:
        return JSONResponse(status_code=503,content={"status":"not_ready","database":"unavailable"})
@app.get("/metrics")
def basic_metrics(): return {"service":"aegisos-api","process_metrics":"Use authenticated /api/metrics for persisted application counters"}
app.include_router(router)
