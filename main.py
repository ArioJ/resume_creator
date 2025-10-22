from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import time

# Import centralized logging configuration
from utils.logging_config import get_logger, log_api_request

# Import endpoint routers
from endpoints.upload_resume import router as upload_router
from endpoints.analyze_resume import router as analyze_router
from endpoints.generate_report import router as report_router
from endpoints.generate_optimized_resume import router as optimize_router

# Get logger for this module
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Advisor Platform",
    description="AI-powered resume analysis and optimization platform",
    version="1.0.0"
)

logger.info("Initializing Resume Advisor Platform")

# Middleware for logging all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests and responses"""
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Request client: {request.client.host if request.client else 'Unknown'}")
    
    # Process request
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(f"Request completed: {request.method} {request.url.path} - "
                   f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms")
        
        # Log to dedicated API log file
        log_api_request(
            endpoint=str(request.url.path),
            method=request.method,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Request failed: {request.method} {request.url.path} - "
                    f"Error: {str(e)} - Duration: {duration_ms:.2f}ms", exc_info=True)
        
        # Log error to API log file
        log_api_request(
            endpoint=str(request.url.path),
            method=request.method,
            status_code=500,
            duration_ms=round(duration_ms, 2),
            error=str(e)
        )
        
        raise

# Configure CORS for frontend
logger.info("Configuring CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS configured with wildcard origins (development mode)")

# Register API routers
logger.info("Registering API routers")
app.include_router(upload_router, tags=["Upload"])
logger.info("✓ Upload router registered")
app.include_router(analyze_router, tags=["Analysis"])
logger.info("✓ Analysis router registered")
app.include_router(report_router, tags=["Reports"])
logger.info("✓ Report router registered")
app.include_router(optimize_router, tags=["Resume Optimization"])
logger.info("✓ Resume optimization router registered")

# Ensure frontend directory exists
FRONTEND_DIR = Path("frontend")
logger.info(f"Checking frontend directory: {FRONTEND_DIR.absolute()}")

if FRONTEND_DIR.exists():
    logger.info("Frontend directory found - will mount static files after routes")
    
    # Serve index.html at root
    @app.get("/", response_class=HTMLResponse)
    async def serve_home():
        logger.debug("Serving index.html")
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            logger.debug(f"Index file found: {index_path}")
            return index_path.read_text(encoding="utf-8")
        logger.error("Index.html not found in frontend directory")
        return "<h1>Resume Advisor Platform</h1><p>Frontend not found. Please check frontend folder.</p>"

    # Serve dashboard.html
    @app.get("/dashboard", response_class=HTMLResponse)
    async def serve_dashboard():
        logger.debug("Serving dashboard.html")
        dashboard_path = FRONTEND_DIR / "dashboard.html"
        if dashboard_path.exists():
            logger.debug(f"Dashboard file found: {dashboard_path}")
            return dashboard_path.read_text(encoding="utf-8")
        logger.error("Dashboard.html not found in frontend directory")
        return "<h1>Dashboard not found</h1>"
    
    logger.info("✓ Frontend routes configured")
    
    # Mount static files LAST (after all route handlers are defined)
    # This prevents the static file mount from interfering with routes
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    logger.info("✓ Static files mounted at /static")
else:
    logger.warning("Frontend directory not found. Only API endpoints will be available.")
    
    @app.get("/")
    def root():
        logger.debug("Serving API root endpoint")
        return {
            "message": "Resume Advisor Platform API",
            "docs": "/docs",
            "status": "running"
        }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint called")
    return {"status": "healthy", "service": "Resume Advisor Platform"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("=" * 80)
    logger.info("🚀 Resume Advisor Platform - Starting up")
    logger.info("=" * 80)
    logger.info("Application is ready to accept requests")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("=" * 80)
    logger.info("🛑 Resume Advisor Platform - Shutting down")
    logger.info("=" * 80)
