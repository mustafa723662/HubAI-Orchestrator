from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.execute import router as execute_router
from app.api.v1.route import router as route_router

load_dotenv()

app = FastAPI(
    title="HubAI Orchestrator",
    description="AI Router/Orchestrator API",
    version="0.2.0",
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

app.include_router(route_router, prefix="/api/v1")
app.include_router(execute_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
