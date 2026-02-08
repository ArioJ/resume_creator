from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import json
from pathlib import Path
import time

# Import centralized logging
from utils.logging_config import get_logger, log_api_request

# Import database
from utils.database import get_db, Analysis, Report

from utils.pdf_generator import PDFReportGenerator

router = APIRouter()
logger = get_logger(__name__)

# Directories
ANALYSIS_DIR = Path("data/analysis")
REPORTS_DIR = Path("reports")


@router.post("/api/generate-report/{analysis_id}")
async def generate_report(analysis_id: str, db: Session = Depends(get_db)):
    """
    Generate PDF report for an analysis
    
    Args:
        analysis_id: ID of the analysis
    
    Returns:
        JSON with report_id and download URL
    """
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info("📝 GENERATE REPORT REQUEST")
    logger.info("=" * 80)
    logger.info(f"Analysis ID: {analysis_id}")
    
    # Retrieve analysis from database
    logger.debug(f"Looking for analysis in database: {analysis_id}")
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        logger.warning(f"Analysis not found in database: {analysis_id}")
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        logger.debug("Parsing analysis results...")
        results = json.loads(analysis.results_json)
        logger.info(f"✓ Analysis data loaded from database")
    except Exception as e:
        logger.error(f"Failed to parse analysis {analysis_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse analysis data")
    
    # Generate PDF
    try:
        logger.info("Initializing PDF generator...")
        generator = PDFReportGenerator()
        
        logger.info("Generating PDF report...")
        pdf_path = generator.generate_report(results, analysis_id)
        
        pdf_size_kb = pdf_path.stat().st_size / 1024
        
        # Save report record to database
        logger.info("Saving report record to database...")
        report = Report(
            id=analysis_id,  # Using analysis_id as report_id for simplicity
            analysis_id=analysis_id,
            file_path=str(pdf_path),
            report_type="analysis"
        )
        # Check if report already exists
        existing_report = db.query(Report).filter(Report.id == analysis_id).first()
        if existing_report:
            existing_report.file_path = str(pdf_path)
            logger.info("Updated existing report record")
        else:
            db.add(report)
            logger.info("Created new report record")
        db.commit()
        
        duration = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("✅ REPORT GENERATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Report ID: {analysis_id}")
        logger.info(f"PDF Size: {pdf_size_kb:.2f} KB")
        logger.info(f"Total Duration: {duration:.2f}s")
        logger.info("=" * 80)
        
        response_data = {
            "report_id": analysis_id,
            "download_url": f"/api/download-report/{analysis_id}",
            "message": "Report generated successfully!"
        }
        
        # Log to API request log
        log_api_request(
            endpoint=f"/api/generate-report/{analysis_id}",
            method="POST",
            response_data=response_data,
            status_code=200,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response_data
    
    except Exception as e:
        db.rollback()
        duration = time.time() - start_time
        logger.error("=" * 80)
        logger.error("❌ REPORT GENERATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Analysis ID: {analysis_id}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duration before failure: {duration:.2f}s")
        logger.error("=" * 80)
        logger.error("Full error details:", exc_info=True)
        
        # Log error to API request log
        log_api_request(
            endpoint=f"/api/generate-report/{analysis_id}",
            method="POST",
            status_code=500,
            duration_ms=round(duration * 1000, 2),
            error=str(e)
        )
        
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/api/download-report/{report_id}")
async def download_report(report_id: str):
    """
    Download PDF report
    
    Args:
        report_id: ID of the report (same as analysis_id)
    
    Returns:
        PDF file download
    """
    logger.info(f"📥 Download request for report: {report_id}")
    
    pdf_path = REPORTS_DIR / f"{report_id}.pdf"
    logger.debug(f"Looking for PDF at: {pdf_path}")
    
    if not pdf_path.exists():
        logger.warning(f"Report not found: {report_id}")
        raise HTTPException(status_code=404, detail="Report not found. Please generate the report first.")
    
    pdf_size_kb = pdf_path.stat().st_size / 1024
    logger.info(f"✓ Serving PDF report: {report_id} ({pdf_size_kb:.2f} KB)")
    
    return FileResponse(
        path=str(pdf_path),
        filename=f"resume_analysis_report_{report_id}.pdf",
        media_type="application/pdf"
    )

