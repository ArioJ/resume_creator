"""
Database models and configuration for Resume Advisor Platform
"""
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Database URL from environment or default to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/resume_advisor"
)

logger.info(f"Database URL configured: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'SQLite'}")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Database Models
class Resume(Base):
    """Resume storage model"""
    __tablename__ = "resumes"
    
    id = Column(String(36), primary_key=True)  # UUID
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, filename={self.filename})>"


class Analysis(Base):
    """Analysis results storage model"""
    __tablename__ = "analyses"
    
    id = Column(String(36), primary_key=True)  # UUID
    resume_id = Column(String(36), ForeignKey("resumes.id"), nullable=False)
    job_description = Column(Text, nullable=False)
    overall_score = Column(Integer)
    results_json = Column(Text, nullable=False)  # JSON string of complete results
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="analyses")
    optimized_resumes = relationship("OptimizedResume", back_populates="analysis", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, score={self.overall_score})>"


class OptimizedResume(Base):
    """Optimized resume storage model"""
    __tablename__ = "optimized_resumes"
    
    id = Column(String(36), primary_key=True)  # UUID
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    content = Column(Text, nullable=False)
    format = Column(String(50), default="markdown")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="optimized_resumes")
    
    def __repr__(self):
        return f"<OptimizedResume(id={self.id}, format={self.format})>"


class Report(Base):
    """Generated report tracking model"""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True)  # UUID
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    report_type = Column(String(50), default="analysis")  # 'analysis' or 'optimized_resume'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, type={self.report_type})>"


# Database helper functions
def get_db():
    """
    Dependency function to get database session
    Usage in FastAPI endpoints:
        from fastapi import Depends
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    logger.info("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        return False


def drop_all_tables():
    """Drop all tables - USE WITH CAUTION!"""
    logger.warning("⚠️  Dropping all database tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✓ All tables dropped")
        return True
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}", exc_info=True)
        return False


def reset_db():
    """Reset database - drop and recreate all tables"""
    logger.warning("⚠️  Resetting database...")
    drop_all_tables()
    return init_db()


# Test database connection
def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Test connection and initialize database
    logger.info("Testing database connection...")
    if test_connection():
        logger.info("Initializing database schema...")
        if init_db():
            logger.info("✅ Database setup complete!")
        else:
            logger.error("❌ Database initialization failed")
    else:
        logger.error("❌ Database connection failed")


