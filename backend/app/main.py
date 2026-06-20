from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api import auth, projects, scenes, avatars, voices, scripts, backgrounds, credits


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="UGC Video Creator API",
    description="Backend API for the UGC Video Creator platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(scenes.router)
app.include_router(avatars.router)
app.include_router(voices.router)
app.include_router(scripts.router)
app.include_router(backgrounds.router)
app.include_router(credits.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ugc-video-creator"}