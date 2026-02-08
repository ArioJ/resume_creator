from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
from pathlib import Path
from uuid import uuid4
import time

# Import centralized logging
from utils.logging_config import get_logger, log_api_request

# Import database
from utils.database import get_db, Resume, Analysis

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
async def analyze_resume(request: AnalysisRequest, db: Session = Depends(get_db)):
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
    
    # Retrieve resume from database
    logger.debug(f"Looking for resume in database: {request.resume_id}")
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    
    if not resume:
        logger.error(f"Resume not found in database: {request.resume_id}")
        raise HTTPException(status_code=404, detail="Resume not found. Please upload the resume first.")
    
    resume_text = resume.content
    logger.info(f"✓ Resume loaded from database: {len(resume_text)} characters")
    
    # Perform analysis
    try:
        logger.info(f"Initializing analyzer for resume {request.resume_id}")
        analyzer = ResumeAnalyzer()
        
        logger.info("Starting comprehensive analysis...")
        analysis_results = analyzer.analyze_resume(resume_text, request.job_description)
        
        # Generate unique analysis ID
        analysis_id = str(uuid4())
        logger.info(f"Generated analysis ID: {analysis_id}")
        
        # Save to database
        logger.info("Saving analysis to database...")
        analysis = Analysis(
            id=analysis_id,
            resume_id=request.resume_id,
            job_description=request.job_description,
            overall_score=analysis_results.get('overall_score'),
            results_json=json.dumps(analysis_results)
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(f"✓ Analysis saved to database: {analysis_id}")
        
        # Also save to disk for backward compatibility (optional)
        analysis_path = ANALYSIS_DIR / f"{analysis_id}.json"
        try:
            logger.debug(f"Saving backup to disk: {analysis_path}")
            analysis_data = {
                "analysis_id": analysis_id,
                "resume_id": request.resume_id,
                "job_description": request.job_description,
                "results": analysis_results
            }
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, indent=2)
            logger.debug(f"✓ Backup saved to disk")
        except Exception as e:
            logger.warning(f"Failed to save backup to disk (non-critical): {str(e)}")
        
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
        db.rollback()
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
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """
    Retrieve previously completed analysis
    
    Args:
        analysis_id: ID of the analysis
    
    Returns:
        Analysis results
    """
    logger.info(f"📊 Retrieving analysis: {analysis_id}")
    
    # Get from database
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        logger.warning(f"Analysis not found in database: {analysis_id}")
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        # Parse JSON results
        results = json.loads(analysis.results_json)
        
        analysis_data = {
            "analysis_id": analysis.id,
            "resume_id": analysis.resume_id,
            "job_description": analysis.job_description,
            "results": results
        }
        
        logger.info(f"✓ Analysis retrieved from database: {analysis_id}")
        
        return JSONResponse(analysis_data)
    
    except Exception as e:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")

