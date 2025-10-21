from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import logging
from pathlib import Path
from uuid import uuid4
from utils.resume_analyzer import ResumeAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)

# Directories
DATA_DIR = Path("data")
ANALYSIS_DIR = Path("data/analysis")
ANALYSIS_DIR.mkdir(exist_ok=True, parents=True)


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
    # Validate inputs
    if not request.resume_id or not request.job_description:
        raise HTTPException(status_code=400, detail="Both resume_id and job_description are required")
    
    if len(request.job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description is too short (minimum 50 characters)")
    
    # Retrieve resume text
    resume_path = DATA_DIR / f"{request.resume_id}.txt"
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail="Resume not found. Please upload the resume first.")
    
    try:
        resume_text = resume_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read resume {request.resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read resume file")
    
    # Perform analysis
    try:
        logger.info(f"Starting analysis for resume {request.resume_id}")
        analyzer = ResumeAnalyzer()
        analysis_results = analyzer.analyze_resume(resume_text, request.job_description)
        
        # Generate unique analysis ID
        analysis_id = str(uuid4())
        
        # Store analysis results
        analysis_data = {
            "analysis_id": analysis_id,
            "resume_id": request.resume_id,
            "job_description": request.job_description,
            "results": analysis_results
        }
        
        analysis_path = ANALYSIS_DIR / f"{analysis_id}.json"
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2)
        
        logger.info(f"Analysis complete: {analysis_id}")
        
        # Return results with analysis ID
        return JSONResponse({
            "analysis_id": analysis_id,
            "resume_id": request.resume_id,
            "results": analysis_results
        })
    
    except Exception as e:
        logger.exception(f"Analysis failed for resume {request.resume_id}")
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
    analysis_path = ANALYSIS_DIR / f"{analysis_id}.json"
    
    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        return JSONResponse(analysis_data)
    
    except Exception as e:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")

