from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import json
from pathlib import Path
import time

# Import centralized logging
from utils.logging_config import get_logger, log_api_request

from utils.pdf_generator import PDFReportGenerator

router = APIRouter()
logger = get_logger(__name__)

# Directories
ANALYSIS_DIR = Path("data/analysis")
REPORTS_DIR = Path("reports")


@router.post("/api/generate-report/{analysis_id}")
async def generate_report(analysis_id: str):
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
    
    # Retrieve analysis data
    analysis_path = ANALYSIS_DIR / f"{analysis_id}.json"
    logger.debug(f"Looking for analysis at: {analysis_path}")
    
    if not analysis_path.exists():
        logger.warning(f"Analysis not found: {analysis_id}")
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        logger.debug("Reading analysis data...")
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        file_size_kb = analysis_path.stat().st_size / 1024
        logger.info(f"✓ Analysis data loaded: {file_size_kb:.2f} KB")
    except Exception as e:
        logger.error(f"Failed to read analysis {analysis_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read analysis data")
    
    # Generate PDF
    try:
        logger.info("Initializing PDF generator...")
        generator = PDFReportGenerator()
        
        logger.info("Generating PDF report...")
        pdf_path = generator.generate_report(analysis_data["results"], analysis_id)
        
        pdf_size_kb = pdf_path.stat().st_size / 1024
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

