from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import json
import logging
from pathlib import Path
from utils.pdf_generator import PDFReportGenerator

router = APIRouter()
logger = logging.getLogger(__name__)

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
    # Retrieve analysis data
    analysis_path = ANALYSIS_DIR / f"{analysis_id}.json"
    
    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read analysis data")
    
    # Generate PDF
    try:
        generator = PDFReportGenerator()
        pdf_path = generator.generate_report(analysis_data["results"], analysis_id)
        
        logger.info(f"Report generated for analysis {analysis_id}")
        
        return {
            "report_id": analysis_id,
            "download_url": f"/api/download-report/{analysis_id}",
            "message": "Report generated successfully!"
        }
    
    except Exception as e:
        logger.exception(f"Failed to generate report for analysis {analysis_id}")
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
    pdf_path = REPORTS_DIR / f"{report_id}.pdf"
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report not found. Please generate the report first.")
    
    return FileResponse(
        path=str(pdf_path),
        filename=f"resume_analysis_report_{report_id}.pdf",
        media_type="application/pdf"
    )

