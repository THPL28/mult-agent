from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

app = FastAPI(
    title="MultiAgent Orchestrator API",
    description="Global Platform for Intelligent Agent Orchestration with LLM to Action",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import ingest
app.include_router(ingest.router)

@app.get("/")
async def root():
    logger.info("Health check endpoint called")
    return {
        "system": "MultiAgent",
        "status": "operational",
        "version": "1.0.0",
        "message": "Anything -> MarkItDown -> Intelligence -> Action"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
