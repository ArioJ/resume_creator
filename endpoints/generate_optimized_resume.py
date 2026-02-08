from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
import json
import time

# Import centralized logging
from utils.logging_config import get_logger, log_api_request
from utils.resume_generator import ResumeGenerator

# Import database
from utils.database import get_db, Resume, Analysis, OptimizedResume, Report

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
async def generate_optimized_resume(request: OptimizeRequest, db: Session = Depends(get_db)):
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
        # Load analysis from database
        logger.debug(f"Looking for analysis in database: {request.analysis_id}")
        analysis = db.query(Analysis).filter(Analysis.id == request.analysis_id).first()
        
        if not analysis:
            logger.warning(f"Analysis not found: {request.analysis_id}")
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        resume_id = analysis.resume_id
        job_description = analysis.job_description
        
        logger.info(f"Resume ID: {resume_id}")
        logger.info(f"Job description length: {len(job_description)} chars")
        
        # Load original resume from database
        logger.debug(f"Looking for resume in database: {resume_id}")
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume:
            logger.warning(f"Resume not found: {resume_id}")
            raise HTTPException(status_code=404, detail="Original resume not found")
        
        resume_text = resume.content
        logger.info(f"Original resume length: {len(resume_text)} chars")
        
        # Generate optimized resume
        logger.info("Initializing resume generator...")
        generator = ResumeGenerator()
        
        logger.info("Generating optimized resume...")
        optimized_resume_text = generator.generate_optimized_resume(resume_text, job_description)
        
        # Save optimized resume to database
        logger.info("Saving optimized resume to database...")
        
        # Check if optimized resume already exists
        existing_optimized = db.query(OptimizedResume).filter(
            OptimizedResume.analysis_id == request.analysis_id
        ).first()
        
        if existing_optimized:
            existing_optimized.content = optimized_resume_text
            logger.info("Updated existing optimized resume")
        else:
            from uuid import uuid4
            optimized_resume = OptimizedResume(
                id=str(uuid4()),
                analysis_id=request.analysis_id,
                content=optimized_resume_text,
                format="markdown"
            )
            db.add(optimized_resume)
            logger.info("Created new optimized resume")
        
        db.commit()
        logger.info("✓ Optimized resume saved to database")
        
        # Also save to disk for backward compatibility (optional)
        optimized_path = OPTIMIZED_DIR / f"{request.analysis_id}.txt"
        try:
            logger.debug(f"Saving backup to disk: {optimized_path}")
            with open(optimized_path, "w", encoding="utf-8") as f:
                f.write(optimized_resume_text)
            file_size_kb = optimized_path.stat().st_size / 1024
            logger.debug(f"✓ Backup saved to disk ({file_size_kb:.2f} KB)")
        except Exception as e:
            logger.warning(f"Failed to save backup to disk (non-critical): {str(e)}")
        
        duration = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("✅ OPTIMIZED RESUME GENERATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Analysis ID: {request.analysis_id}")
        logger.info(f"Optimized resume length: {len(optimized_resume_text)} chars")
        logger.info(f"Total duration: {duration:.2f}s")
        logger.info("=" * 80)
        
        response_data = {
            "message": "Optimized resume generated successfully!",
            "analysis_id": request.analysis_id,
            "optimized_resume": optimized_resume_text,
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
        db.rollback()
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
async def download_optimized_resume(analysis_id: str, db: Session = Depends(get_db)):
    """
    Download optimized resume as PDF (converted from Markdown)
    
    Args:
        analysis_id: ID of the analysis
    
    Returns:
        PDF file download
    """
    from fastapi.responses import FileResponse
    from utils.markdown_to_pdf import get_markdown_converter
    from uuid import uuid4
    
    logger.info(f"📥 Download request for optimized resume PDF: {analysis_id}")
    
    # Get optimized resume from database
    logger.debug(f"Looking for optimized resume in database: {analysis_id}")
    optimized_resume = db.query(OptimizedResume).filter(
        OptimizedResume.analysis_id == analysis_id
    ).first()
    
    if not optimized_resume:
        logger.warning(f"Optimized resume not found: {analysis_id}")
        raise HTTPException(
            status_code=404,
            detail="Optimized resume not found. Please generate it first."
        )
    
    try:
        # Get the markdown content from database
        markdown_content = optimized_resume.content
        logger.info(f"✓ Retrieved optimized resume from database ({len(markdown_content)} chars)")
        
        # Convert to PDF
        logger.info("Converting markdown to PDF...")
        converter = get_markdown_converter()
        pdf_path = converter.convert_to_pdf(markdown_content, f"optimized_resume_{analysis_id}")
        
        # Save report record to database
        logger.info("Saving report record to database...")
        report_id = str(uuid4())
        report = Report(
            id=report_id,
            analysis_id=analysis_id,
            file_path=str(pdf_path),
            report_type="optimized_resume"
        )
        # Check if report already exists
        existing_report = db.query(Report).filter(
            Report.analysis_id == analysis_id,
            Report.report_type == "optimized_resume"
        ).first()
        if existing_report:
            existing_report.file_path = str(pdf_path)
            logger.info("Updated existing report record")
        else:
            db.add(report)
            logger.info("Created new report record")
        db.commit()
        
        file_size_kb = pdf_path.stat().st_size / 1024
        logger.info(f"✓ Serving optimized resume PDF: {analysis_id} ({file_size_kb:.2f} KB)")
        
        return FileResponse(
            path=str(pdf_path),
            filename=f"optimized_resume_{analysis_id}.pdf",
            media_type="application/pdf"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )

