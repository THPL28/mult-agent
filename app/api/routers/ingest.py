from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from loguru import logger
import shutil
import os

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post("/")
async def ingest_file(
    file: UploadFile = File(...),
    sector: Optional[str] = Form("general")
):
    """
    Ingest any file and convert to Markdown via MarkItDown Agent.
    """
    logger.info(f"Received file: {file.filename} for sector: {sector}")
    
    # Save temp file
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Call MarkItDown Agent (Simulated for now)
        # from agents.markitdown.agent import agent as markitdown_agent
        # result = await markitdown_agent.process(temp_path, file.content_type)
        
        # Mock result
        markdown = f"""---
filename: {file.filename}
sector: {sector}
status: processed
---

# Extracted Content from {file.filename}

This is a simulated extraction.
"""
        return {"filename": file.filename, "markdown": markdown, "status": "success"}
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/text")
async def ingest_text(text: str = Form(...), sector: str = Form("general")):
    logger.info(f"Received text for sector: {sector}")
    return {
        "markdown": f"# Text Input\n\n{text}",
        "status": "success"
    }
