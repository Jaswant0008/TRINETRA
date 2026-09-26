import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, EXTRACTED_IMAGES_DIR, UPLOADS_DIR
from app.api.routes import router, reload_demo_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TRINETRA")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TRINETRA Multimodal Fusion Intelligence Platform (PS-05)...")
    try:
        supported_exts = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"}
        user_files = [f for f in sorted(UPLOADS_DIR.iterdir()) if f.is_file() and f.suffix.lower() in supported_exts]
        if user_files:
            from app.api.routes import reingest_all_uploads
            reingest_all_uploads()
            logger.info(f"Loaded {len(user_files)} local intelligence sources successfully.")
        else:
            logger.info("TRINETRA initialized with clean slate (0 sources). Ready for user ingestion or Demo Mode activation.")
    except Exception as e:
        logger.warning(f"Could not load initial scenarios on startup: {e}")
    yield
    logger.info("Shutting down TRINETRA...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TRINETRA Multimodal Intelligence Fusion System - PS-05 Decentralized Knowledge Graph Builder Agent",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset directories
app.mount("/static/extracted", StaticFiles(directory=str(EXTRACTED_IMAGES_DIR)), name="extracted")
app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Include API router at /api and also standard root paths
app.include_router(router, prefix=settings.API_V1_STR)
app.include_router(router)

# Mount frontend
FRONTEND_DIR = EXTRACTED_IMAGES_DIR.parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
