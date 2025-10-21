from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
import docx2txt
import io, tempfile, os
from pathlib import Path
from uuid import uuid4
import time

# Import centralized logging
from utils.logging_config import get_logger, log_api_request

router = APIRouter()
logger = get_logger(__name__)

# storage directory for extracted text files
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
logger.info(f"Resume data directory initialized: {DATA_DIR.absolute()}")

# Limit uploads to prevent DoS via very large files (10 MB default)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
logger.info(f"Maximum upload size set to: {MAX_UPLOAD_SIZE / 1024 / 1024} MB")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file"""
    logger.debug(f"Extracting text from PDF ({len(file_bytes)} bytes)")
    start_time = time.time()
    
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        num_pages = len(reader.pages)
        logger.info(f"PDF has {num_pages} pages")
        
        text = ""
        for i, page in enumerate(reader.pages, 1):
            page_text = page.extract_text() or ""
            text += page_text
            logger.debug(f"Extracted {len(page_text)} characters from page {i}")
        
        text = text.strip()
        duration = time.time() - start_time
        logger.info(f"PDF text extraction complete: {len(text)} characters in {duration:.2f}s")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}", exc_info=True)
        raise


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file"""
    logger.debug(f"Extracting text from DOCX ({len(file_bytes)} bytes)")
    start_time = time.time()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
        logger.debug(f"Created temporary file: {tmp_path}")
    
    try:
        text = docx2txt.process(tmp_path)
        text = text.strip()
        duration = time.time() - start_time
        logger.info(f"DOCX text extraction complete: {len(text)} characters in {duration:.2f}s")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX: {str(e)}", exc_info=True)
        raise
    finally:
        try:
            os.remove(tmp_path)
            logger.debug(f"Cleaned up temporary file: {tmp_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to remove temp file {tmp_path}: {str(cleanup_error)}")


@router.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and extract text from resume file (PDF, DOCX, TXT)
    
    Returns:
        JSON with resume_id, filename, and character count
    """
    start_time = time.time()
    filename = file.filename or "unknown"
    
    logger.info("=" * 80)
    logger.info(f"📄 RESUME UPLOAD REQUEST")
    logger.info(f"Filename: {filename}")
    logger.info(f"Content Type: {file.content_type}")
    logger.info("=" * 80)
    
    filename_lower = filename.lower()
    
    try:
        # Read file bytes
        logger.debug("Reading file bytes...")
        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / 1024 / 1024
        logger.info(f"File size: {file_size_mb:.2f} MB ({len(file_bytes)} bytes)")

        # Size validation
        if len(file_bytes) > MAX_UPLOAD_SIZE:
            logger.warning(f"File size exceeds limit: {file_size_mb:.2f} MB > {MAX_UPLOAD_SIZE / 1024 / 1024} MB")
            raise HTTPException(status_code=413, detail=f"File too large (max {MAX_UPLOAD_SIZE / 1024 / 1024} MB)")

        # Extract text based on file type
        logger.info(f"Determining file type for: {filename_lower}")
        
        if filename_lower.endswith(".pdf"):
            logger.info("File type: PDF")
            text = extract_text_from_pdf(file_bytes)
        elif filename_lower.endswith(".docx"):
            logger.info("File type: DOCX")
            text = extract_text_from_docx(file_bytes)
        elif filename_lower.endswith(".txt"):
            logger.info("File type: TXT")
            text = file_bytes.decode("utf-8", errors="replace").strip()
            logger.info(f"TXT text extraction complete: {len(text)} characters")
        else:
            logger.error(f"Unsupported file type: {filename}")
            raise HTTPException(status_code=400, detail="Only PDF, DOCX and TXT are supported")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract text from uploaded file: {filename}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to extract text from file: {str(e)}")

    # Validate extracted text
    if not text:
        logger.error("No text extracted from file")
        raise HTTPException(status_code=400, detail="No extractable text found in the file")
    
    logger.info(f"✓ Text extraction successful: {len(text)} characters")
    logger.debug(f"Text preview (first 200 chars): {text[:200]}")

    # Create unique ID for this resume
    resume_id = str(uuid4())
    txt_path = DATA_DIR / f"{resume_id}.txt"
    logger.info(f"Generated resume ID: {resume_id}")
    logger.debug(f"Saving to: {txt_path}")

    # Save text to disk
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"✓ Resume saved to disk: {txt_path}")
    except Exception as e:
        logger.error(f"Failed to save resume to disk: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save resume")

    duration = time.time() - start_time
    logger.info("=" * 80)
    logger.info(f"✅ RESUME UPLOAD COMPLETE")
    logger.info(f"Resume ID: {resume_id}")
    logger.info(f"Filename: {filename}")
    logger.info(f"Size: {file_size_mb:.2f} MB")
    logger.info(f"Characters: {len(text)}")
    logger.info(f"Duration: {duration:.2f}s")
    logger.info("=" * 80)

    response_data = {
        "resume_id": resume_id,
        "filename": filename,
        "num_chars": len(text),
        "message": "Resume uploaded and processed successfully!"
    }
    
    # Log to API request log
    log_api_request(
        endpoint="/api/upload-resume",
        method="POST",
        request_data={"filename": filename, "size_mb": round(file_size_mb, 2)},
        response_data=response_data,
        status_code=200,
        duration_ms=round(duration * 1000, 2)
    )

    return JSONResponse(response_data)

