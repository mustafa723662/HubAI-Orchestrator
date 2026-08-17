from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.execute import router as execute_router
from app.api.v1.history import router as history_router
from app.api.v1.route import router as route_router
from app.core.config import get_allowed_origins
from app.core.limiter import limiter
from app.db import models  # noqa: F401 — must be imported so Base knows about the tables below
from app.db.database import Base, engine

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HubAI Orchestrator",
    description="AI Router/Orchestrator API",
    version="0.4.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Defaults to "*" for local dev (file:// sends "Origin: null", which an
# explicit allowlist won't match anyway). Set ALLOWED_ORIGINS in production
# to your deployed frontend's real origin(s), comma-separated.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
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
