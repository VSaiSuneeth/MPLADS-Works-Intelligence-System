import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, dashboard, risk, works, cases, audit, imports, similarity, simulation, evidence

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MPLADS Works Intelligence & Review System backend...")
    yield
    logger.info("Shutting down MPLADS Works Intelligence & Review System backend.")

app = FastAPI(
    title="MPLADS Works Intelligence & Review System",
    version="1.0.0",
    description="AI-powered operational review and risk prioritization system for district officers and state auditors.",
    lifespan=lifespan
)

default_origins = [
    "https://mplads-works-frontend.onrender.com",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174"
]
cors_env = os.getenv("CORS_ORIGINS")
cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] if cors_env else default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include MPLADS API Routers under /api/v1
mplads_router = APIRouter()
mplads_router.include_router(auth.router)
mplads_router.include_router(dashboard.router)
mplads_router.include_router(risk.router)
mplads_router.include_router(works.router)
mplads_router.include_router(similarity.router)
mplads_router.include_router(cases.router)
mplads_router.include_router(audit.router)
mplads_router.include_router(imports.router)
mplads_router.include_router(simulation.router)
mplads_router.include_router(evidence.router)

app.include_router(mplads_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "system": "MPLADS Works Intelligence & Review System",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "docs_url": "/docs"
    }

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "MPLADS Works Intelligence Backend",
        "version": "1.0.0"
    }

# Mount uploads static directory if present
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
