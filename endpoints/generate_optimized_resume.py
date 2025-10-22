from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import time

# Import centralized logging
from utils.logging_config import get_logger, log_api_request
from utils.resume_generator import ResumeGenerator

router = APIRouter()
logger = get_logger(__name__)

# Directories
DATA_DIR = Path("data")
ANALYSIS_DIR = Path("data/analysis")
OPTIMIZED_DIR = Path("data/optimized_resumes")

# Ensure optimized resumes directory exists
OPTIMIZED_DIR.mkdir(parents=True, exist_ok=True)


class OptimizeRequest(BaseModel):
    """Request model for resume optimization"""
    analysis_id: str


@router.post("/api/generate-optimized-resume")
async def generate_optimized_resume(request: OptimizeRequest):
    """
    Generate an optimized resume tailored to the job description
    
    Args:
        request: Contains analysis_id to get original resume and job description
    
    Returns:
        JSON with optimized resume text and download info
    """
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info("🔄 OPTIMIZED RESUME GENERATION REQUEST")
    logger.info("=" * 80)
    logger.info(f"Analysis ID: {request.analysis_id}")
    
    try:
        # Load analysis data to get job description and resume_id
        analysis_path = ANALYSIS_DIR / f"{request.analysis_id}.json"
        
        if not analysis_path.exists():
            logger.warning(f"Analysis not found: {request.analysis_id}")
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        logger.debug(f"Loading analysis from: {analysis_path}")
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        resume_id = analysis_data.get("resume_id")
        job_description = analysis_data.get("job_description")
        
        logger.info(f"Resume ID: {resume_id}")
        logger.info(f"Job description length: {len(job_description)} chars")
        
        # Load original resume text
        resume_path = DATA_DIR / f"{resume_id}.txt"
        
        if not resume_path.exists():
            logger.warning(f"Resume file not found: {resume_id}")
            raise HTTPException(status_code=404, detail="Original resume not found")
        
        logger.debug(f"Loading resume from: {resume_path}")
        with open(resume_path, "r", encoding="utf-8") as f:
            resume_text = f.read()
        
        logger.info(f"Original resume length: {len(resume_text)} chars")
        
        # Generate optimized resume
        logger.info("Initializing resume generator...")
        generator = ResumeGenerator()
        
        logger.info("Generating optimized resume...")
        optimized_resume = generator.generate_optimized_resume(resume_text, job_description)
        
        # Save optimized resume
        optimized_path = OPTIMIZED_DIR / f"{request.analysis_id}.txt"
        logger.debug(f"Saving optimized resume to: {optimized_path}")
        
        with open(optimized_path, "w", encoding="utf-8") as f:
            f.write(optimized_resume)
        
        file_size_kb = optimized_path.stat().st_size / 1024
        
        duration = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("✅ OPTIMIZED RESUME GENERATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Analysis ID: {request.analysis_id}")
        logger.info(f"Optimized resume size: {file_size_kb:.2f} KB")
        logger.info(f"Total duration: {duration:.2f}s")
        logger.info("=" * 80)
        
        response_data = {
            "message": "Optimized resume generated successfully!",
            "analysis_id": request.analysis_id,
            "optimized_resume": optimized_resume,
            "download_url": f"/api/download-optimized-resume/{request.analysis_id}"
        }
        
        # Log to API request log
        log_api_request(
            endpoint="/api/generate-optimized-resume",
            method="POST",
            response_data={"message": "Success", "analysis_id": request.analysis_id},
            status_code=200,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error("=" * 80)
        logger.error("❌ OPTIMIZED RESUME GENERATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Analysis ID: {request.analysis_id}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duration before failure: {duration:.2f}s")
        logger.error("=" * 80)
        logger.error("Full error details:", exc_info=True)
        
        # Log error to API request log
        log_api_request(
            endpoint="/api/generate-optimized-resume",
            method="POST",
            status_code=500,
            duration_ms=round(duration * 1000, 2),
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate optimized resume: {str(e)}"
        )


@router.get("/api/download-optimized-resume/{analysis_id}")
async def download_optimized_resume(analysis_id: str):
    """
    Download optimized resume as PDF (converted from Markdown)
    
    Args:
        analysis_id: ID of the analysis
    
    Returns:
        PDF file download
    """
    from fastapi.responses import FileResponse
    from utils.markdown_to_pdf import get_markdown_converter
    
    logger.info(f"📥 Download request for optimized resume PDF: {analysis_id}")
    
    # Check if markdown resume exists
    optimized_path = OPTIMIZED_DIR / f"{analysis_id}.txt"
    
    if not optimized_path.exists():
        logger.warning(f"Optimized resume not found: {analysis_id}")
        raise HTTPException(
            status_code=404,
            detail="Optimized resume not found. Please generate it first."
        )
    
    try:
        # Read the markdown content
        logger.debug(f"Reading markdown from: {optimized_path}")
        with open(optimized_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        
        # Convert to PDF
        logger.info("Converting markdown to PDF...")
        converter = get_markdown_converter()
        pdf_path = converter.convert_to_pdf(markdown_content, f"optimized_resume_{analysis_id}")
        
        file_size_kb = pdf_path.stat().st_size / 1024
        logger.info(f"✓ Serving optimized resume PDF: {analysis_id} ({file_size_kb:.2f} KB)")
        
        return FileResponse(
            path=str(pdf_path),
            filename=f"optimized_resume_{analysis_id}.pdf",
            media_type="application/pdf"
        )
    
    except Exception as e:
        logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )

