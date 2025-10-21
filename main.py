from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
from pathlib import Path

# Import endpoint routers
from endpoints.upload_resume import router as upload_router
from endpoints.analyze_resume import router as analyze_router
from endpoints.generate_report import router as report_router

# Initialize FastAPI app
app = FastAPI(
    title="Resume Advisor Platform",
    description="AI-powered resume analysis and optimization platform",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(upload_router, tags=["Upload"])
app.include_router(analyze_router, tags=["Analysis"])
app.include_router(report_router, tags=["Reports"])

# Ensure frontend directory exists
FRONTEND_DIR = Path("frontend")
if FRONTEND_DIR.exists():
    # Mount static files (CSS, JS)
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    # Serve index.html at root
    @app.get("/", response_class=HTMLResponse)
    async def serve_home():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<h1>Resume Advisor Platform</h1><p>Frontend not found. Please check frontend folder.</p>"

    # Serve dashboard.html
    @app.get("/dashboard", response_class=HTMLResponse)
    async def serve_dashboard():
        dashboard_path = FRONTEND_DIR / "dashboard.html"
        if dashboard_path.exists():
            return dashboard_path.read_text(encoding="utf-8")
        return "<h1>Dashboard not found</h1>"
else:
    logger.warning("Frontend directory not found. Only API endpoints will be available.")
    
    @app.get("/")
    def root():
        return {
            "message": "Resume Advisor Platform API",
            "docs": "/docs",
            "status": "running"
        }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Resume Advisor Platform"}
