from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.execute import router as execute_router
from app.api.v1.history import router as history_router
from app.api.v1.route import router as route_router
from app.db import models  # noqa: F401 — must be imported so Base knows about the tables below
from app.db.database import Base, engine

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HubAI Orchestrator",
    description="AI Router/Orchestrator API",
    version="0.3.0",
)

# Dev-only: wide open so the frontend works whether it's served from
# localhost:3000, a Live Server port, or opened directly as a local file
# (file:// sends "Origin: null", which an explicit allowlist won't match).
# Tighten this to specific origins before deploying anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(route_router, prefix="/api/v1")
app.include_router(execute_router, prefix="/api/v1")
app.include_router(history_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
