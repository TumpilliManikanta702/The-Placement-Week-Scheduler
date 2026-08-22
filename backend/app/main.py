import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import config
from app.database.connection import engine, Base, SessionLocal
from app.database.models import Company
from app.seed.generator import generate_placement_dataset
from app.optimization.solver import PlacementScheduler
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB tables
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)

    # 2. Check if fresh DB needs auto-seeding
    db = SessionLocal()
    try:
        company_count = db.query(Company).count()
        if company_count == 0:
            logger.info("Fresh database detected. Auto-generating placement dataset (seed=42) and initial schedule...")
            generate_placement_dataset(db, seed=config.SEED)
            scheduler = PlacementScheduler(db)
            scheduler.generate_initial_schedule(version_id=1)
            logger.info("Auto-initialization complete.")
    except Exception as e:
        logger.error(f"Error during auto-initialization: {e}")
    finally:
        db.close()

    yield

app = FastAPI(
    title="Placement Week Scheduler API",
    description="Production-quality placement week scheduling engine and minimal-disruption replanner.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS if config.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Mirai Labs — Placement Week Scheduler Engine",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
