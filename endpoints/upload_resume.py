from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
import docx2txt
import io, tempfile, os, logging
from pathlib import Path
from uuid import uuid4

router = APIRouter()
logger = logging.getLogger(__name__)

# storage directory for extracted text files
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Limit uploads to prevent DoS via very large files (10 MB default)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        text = docx2txt.process(tmp_path)
        return text.strip()
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            logger.exception("Failed to remove temp file %s", tmp_path)


@router.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and extract text from resume file (PDF, DOCX, TXT)
    
    Returns:
        JSON with resume_id, filename, and character count
    """
    filename = (file.filename or "").lower()
    file_bytes = await file.read()

    # basic size guard
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_UPLOAD_SIZE} bytes)")

    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_bytes)
        elif filename.endswith(".docx"):
            text = extract_text_from_docx(file_bytes)
        elif filename.endswith(".txt"):
            text = file_bytes.decode("utf-8", errors="replace").strip()
        else:
            raise HTTPException(status_code=400, detail="Only PDF, DOCX and TXT are supported")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to extract text from uploaded file: %s", filename)
        raise HTTPException(status_code=400, detail="Failed to extract text from file")

    if not text:
        raise HTTPException(status_code=400, detail="No extractable text found in the file")

    # create unique ID for this resume
    resume_id = str(uuid4())
    txt_path = DATA_DIR / f"{resume_id}.txt"

    # save text to disk
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    logger.info(f"Resume uploaded: {resume_id} ({len(text)} characters)")

    return JSONResponse({
        "resume_id": resume_id,
        "filename": file.filename,
        "num_chars": len(text),
        "message": "Resume uploaded and processed successfully!"
    })

