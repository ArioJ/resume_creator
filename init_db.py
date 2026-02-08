"""
Database initialization script for Resume Advisor Platform
Run this script to set up the database tables
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import init_db, test_connection, reset_db
from utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Initialize the database"""
    logger.info("=" * 80)
    logger.info("🗄️  RESUME ADVISOR - DATABASE INITIALIZATION")
    logger.info("=" * 80)
    
    # Test connection first
    logger.info("\n1. Testing database connection...")
    if not test_connection():
        logger.error("❌ Database connection failed!")
        logger.error("Please check your DATABASE_URL in .env file")
        logger.error("Example: DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_advisor")
        return False
    
    logger.info("✓ Database connection successful\n")
    
    # Ask user if they want to reset (drop and recreate)
    logger.info("2. Database initialization options:")
    logger.info("   - Create tables (if they don't exist)")
    logger.info("   - Reset database (drop all tables and recreate)")
    
    try:
        choice = input("\nDo you want to RESET the database? (yes/no) [no]: ").strip().lower()
        
        if choice in ['yes', 'y']:
            logger.warning("\n⚠️  RESETTING DATABASE - All data will be lost!")
            confirm = input("Are you sure? Type 'RESET' to confirm: ").strip()
            
            if confirm == 'RESET':
                if reset_db():
                    logger.info("✅ Database reset successful!")
                    return True
                else:
                    logger.error("❌ Database reset failed!")
                    return False
            else:
                logger.info("Reset cancelled")
                return False
        else:
            logger.info("\n3. Creating database tables...")
            if init_db():
                logger.info("✅ Database initialization successful!")
                logger.info("\nYou can now start the application with: uvicorn main:app --reload")
                return True
            else:
                logger.error("❌ Database initialization failed!")
                return False
                
    except KeyboardInterrupt:
        logger.info("\n\nOperation cancelled by user")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


