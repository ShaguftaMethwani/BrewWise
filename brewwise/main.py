import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from brewwise.config import settings
from brewwise.api.v1.router import api_v1_router
from brewwise.db.session import init_db
from brewwise.db.seed import seed_equipment

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("brewwise")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing BrewWise backend services...")
    # Ensure local storage dir exists
    os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
    # Initialize DB schema & seed data
    try:
        await init_db()
        await seed_equipment()
        from scripts.ingest_curated import seed_curated_knowledge_base
        await seed_curated_knowledge_base()
        logger.info("Database initialized, equipment catalogue and curated recipes seeded.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    yield

    logger.info("Shutting down BrewWise backend...")


app = FastAPI(
    title="BrewWise API",
    description="Intelligent Pour-Over Coffee Recipe Generation Engine",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app|https://.*\.railway\.app|http://localhost:\d+|http://127.0.0.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local uploads static directory for image previews
if os.path.exists(settings.LOCAL_STORAGE_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.LOCAL_STORAGE_DIR), name="uploads")

# Include v1 router
app.include_router(api_v1_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to BrewWise API",
        "docs_url": "/docs",
        "health": "/api/v1/health"
    }
