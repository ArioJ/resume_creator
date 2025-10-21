from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from pathlib import Path
from uuid import uuid4
import time

# Import centralized logging
from utils.logging_config import get_logger, log_api_request

from utils.resume_analyzer import ResumeAnalyzer

router = APIRouter()
logger = get_logger(__name__)

# Directories
DATA_DIR = Path("data")
ANALYSIS_DIR = Path("data/analysis")
ANALYSIS_DIR.mkdir(exist_ok=True, parents=True)
logger.info(f"Analysis directory initialized: {ANALYSIS_DIR.absolute()}")


class AnalysisRequest(BaseModel):
    resume_id: str
    job_description: str


@router.post("/api/analyze")
async def analyze_resume(request: AnalysisRequest):
    """
    Analyze resume against job description
    
    Args:
        resume_id: ID of previously uploaded resume
        job_description: Text of job description
    
    Returns:
        Complete analysis with scores, skills, gaps, and recommendations
    """
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info("🔬 RESUME ANALYSIS REQUEST")
    logger.info("=" * 80)
    logger.info(f"Resume ID: {request.resume_id}")
    logger.info(f"Job description length: {len(request.job_description)} characters")
    
    # Validate inputs
    if not request.resume_id or not request.job_description:
        logger.error("Missing required fields")
        raise HTTPException(status_code=400, detail="Both resume_id and job_description are required")
    
    if len(request.job_description.strip()) < 50:
        logger.warning(f"Job description too short: {len(request.job_description.strip())} characters")
        raise HTTPException(status_code=400, detail="Job description is too short (minimum 50 characters)")
    
    logger.info("✓ Input validation passed")
    
    # Retrieve resume text
    resume_path = DATA_DIR / f"{request.resume_id}.txt"
    logger.debug(f"Looking for resume at: {resume_path}")
    
    if not resume_path.exists():
        logger.error(f"Resume not found: {request.resume_id}")
        raise HTTPException(status_code=404, detail="Resume not found. Please upload the resume first.")
    
    try:
        logger.debug("Reading resume file...")
        resume_text = resume_path.read_text(encoding="utf-8")
        logger.info(f"✓ Resume loaded: {len(resume_text)} characters")
    except Exception as e:
        logger.error(f"Failed to read resume {request.resume_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read resume file")
    
    # Perform analysis
    try:
        logger.info(f"Initializing analyzer for resume {request.resume_id}")
        analyzer = ResumeAnalyzer()
        
        logger.info("Starting comprehensive analysis...")
        analysis_results = analyzer.analyze_resume(resume_text, request.job_description)
        
        # Generate unique analysis ID
        analysis_id = str(uuid4())
        logger.info(f"Generated analysis ID: {analysis_id}")
        
        # Store analysis results
        analysis_data = {
            "analysis_id": analysis_id,
            "resume_id": request.resume_id,
            "job_description": request.job_description,
            "results": analysis_results
        }
        
        analysis_path = ANALYSIS_DIR / f"{analysis_id}.json"
        logger.debug(f"Saving analysis to: {analysis_path}")
        
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2)
        
        file_size_kb = analysis_path.stat().st_size / 1024
        logger.info(f"✓ Analysis saved: {file_size_kb:.2f} KB")
        
        duration = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("✅ RESUME ANALYSIS COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Analysis ID: {analysis_id}")
        logger.info(f"Overall Score: {analysis_results.get('overall_score', 'N/A')}/100")
        logger.info(f"Total Duration: {duration:.2f}s ({duration/60:.2f} minutes)")
        logger.info("=" * 80)
        
        response_data = {
            "analysis_id": analysis_id,
            "resume_id": request.resume_id,
            "results": analysis_results
        }
        
        # Log to API request log
        log_api_request(
            endpoint="/api/analyze",
            method="POST",
            request_data={"resume_id": request.resume_id, "job_desc_length": len(request.job_description)},
            response_data={"analysis_id": analysis_id, "overall_score": analysis_results.get('overall_score')},
            status_code=200,
            duration_ms=round(duration * 1000, 2)
        )
        
        return JSONResponse(response_data)
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error("=" * 80)
        logger.error("❌ RESUME ANALYSIS FAILED")
        logger.error("=" * 80)
        logger.error(f"Resume ID: {request.resume_id}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duration before failure: {duration:.2f}s")
        logger.error("=" * 80)
        logger.error("Full error details:", exc_info=True)
        
        # Log error to API request log
        log_api_request(
            endpoint="/api/analyze",
            method="POST",
            request_data={"resume_id": request.resume_id},
            status_code=500,
            duration_ms=round(duration * 1000, 2),
            error=str(e)
        )
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Retrieve previously completed analysis
    
    Args:
        analysis_id: ID of the analysis
    
    Returns:
        Analysis results
    """
    logger.info(f"📊 Retrieving analysis: {analysis_id}")
    
    analysis_path = ANALYSIS_DIR / f"{analysis_id}.json"
    
    if not analysis_path.exists():
        logger.warning(f"Analysis not found: {analysis_id}")
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        logger.debug(f"Reading analysis from: {analysis_path}")
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        file_size_kb = analysis_path.stat().st_size / 1024
        logger.info(f"✓ Analysis retrieved: {analysis_id} ({file_size_kb:.2f} KB)")
        
        return JSONResponse(analysis_data)
    
    except Exception as e:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")

