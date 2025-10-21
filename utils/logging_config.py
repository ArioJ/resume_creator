"""
Centralized logging configuration for Resume Advisor Platform

This module provides a robust logging setup that all other modules should import.
Logs are stored in the app_log/ directory with rotation and detailed formatting.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys
import json


# Create app_log directory if it doesn't exist
LOG_DIR = Path("app_log")
LOG_DIR.mkdir(exist_ok=True)

# Log file paths
MAIN_LOG_FILE = LOG_DIR / "resume_advisor.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
API_LOG_FILE = LOG_DIR / "api_requests.log"
OPENAI_LOG_FILE = LOG_DIR / "openai_calls.log"


class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs as JSON for easier parsing"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data, ensure_ascii=False)


class DetailedFormatter(logging.Formatter):
    """Detailed human-readable formatter"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging(log_level=logging.INFO, use_json=False):
    """
    Configure logging for the entire application
    
    Args:
        log_level: Minimum logging level (default: INFO)
        use_json: Whether to use JSON format for logs (default: False)
    
    Returns:
        Root logger instance
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Choose formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = DetailedFormatter()
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Main log file handler with rotation (all levels)
    main_file_handler = logging.handlers.RotatingFileHandler(
        MAIN_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    main_file_handler.setLevel(logging.DEBUG)
    main_file_handler.setFormatter(formatter)
    root_logger.addHandler(main_file_handler)
    
    # Error log file handler (ERROR and CRITICAL only)
    error_file_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)
    
    # Log startup
    root_logger.info("=" * 80)
    root_logger.info("Resume Advisor Platform - Logging initialized")
    root_logger.info(f"Log directory: {LOG_DIR.absolute()}")
    root_logger.info(f"Log level: {logging.getLevelName(log_level)}")
    root_logger.info("=" * 80)
    
    return root_logger


def get_logger(name):
    """
    Get a logger instance for a specific module
    
    Args:
        name: Name of the module (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_api_request(endpoint, method, request_data=None, response_data=None, 
                   status_code=None, duration_ms=None, error=None):
    """
    Log API request/response details to dedicated API log file
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        request_data: Request payload (will be sanitized)
        response_data: Response payload (will be truncated if large)
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        error: Error message if request failed
    """
    api_logger = logging.getLogger("api")
    
    # Create dedicated API file handler if it doesn't exist
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(API_LOG_FILE.absolute()) 
               for h in api_logger.handlers):
        api_handler = logging.handlers.RotatingFileHandler(
            API_LOG_FILE,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        api_handler.setFormatter(DetailedFormatter())
        api_logger.addHandler(api_handler)
    
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "duration_ms": duration_ms
    }
    
    if request_data:
        # Sanitize sensitive data
        sanitized_request = sanitize_log_data(request_data)
        log_data["request"] = sanitized_request
    
    if response_data:
        # Truncate large responses
        truncated_response = truncate_large_data(response_data)
        log_data["response"] = truncated_response
    
    if error:
        log_data["error"] = str(error)
        api_logger.error(f"API Request Failed: {json.dumps(log_data, indent=2)}")
    else:
        api_logger.info(f"API Request: {json.dumps(log_data, indent=2)}")


def log_openai_call(operation, prompt=None, response=None, model=None, 
                   tokens_used=None, duration_ms=None, error=None):
    """
    Log OpenAI API calls to dedicated OpenAI log file
    
    Args:
        operation: Type of operation (e.g., "skill_extraction", "dimension_scoring")
        prompt: Prompt sent to OpenAI (will be truncated)
        response: Response from OpenAI (will be truncated)
        model: OpenAI model used
        tokens_used: Number of tokens consumed
        duration_ms: Call duration in milliseconds
        error: Error message if call failed
    """
    openai_logger = logging.getLogger("openai")
    
    # Create dedicated OpenAI file handler if it doesn't exist
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(OPENAI_LOG_FILE.absolute()) 
               for h in openai_logger.handlers):
        openai_handler = logging.handlers.RotatingFileHandler(
            OPENAI_LOG_FILE,
            maxBytes=20 * 1024 * 1024,  # 20 MB for potentially large prompts
            backupCount=10,
            encoding='utf-8'
        )
        openai_handler.setFormatter(DetailedFormatter())
        openai_logger.addHandler(openai_handler)
    
    log_data = {
        "operation": operation,
        "model": model,
        "tokens_used": tokens_used,
        "duration_ms": duration_ms
    }
    
    if prompt:
        # Truncate very long prompts but keep enough for debugging
        log_data["prompt"] = truncate_text(str(prompt), max_length=2000)
    
    if response:
        log_data["response"] = truncate_text(str(response), max_length=2000)
    
    if error:
        log_data["error"] = str(error)
        openai_logger.error(f"OpenAI Call Failed: {json.dumps(log_data, indent=2)}")
    else:
        openai_logger.info(f"OpenAI Call: {json.dumps(log_data, indent=2)}")


def sanitize_log_data(data):
    """
    Remove sensitive information from log data
    
    Args:
        data: Data to sanitize (dict, str, etc.)
    
    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        sanitized = {}
        sensitive_keys = ['password', 'api_key', 'token', 'secret', 'authorization']
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_log_data(value)
            else:
                sanitized[key] = value
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    
    return data


def truncate_large_data(data, max_size=1000):
    """
    Truncate large data structures for logging
    
    Args:
        data: Data to truncate
        max_size: Maximum size in characters
    
    Returns:
        Truncated data
    """
    data_str = str(data)
    if len(data_str) > max_size:
        return data_str[:max_size] + f"... [TRUNCATED - Total length: {len(data_str)}]"
    return data


def truncate_text(text, max_length=1000):
    """
    Truncate text for logging while preserving readability
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Keep beginning and end for context
    keep_each = max_length // 2 - 50
    return f"{text[:keep_each]}\n... [TRUNCATED {len(text) - 2*keep_each} chars] ...\n{text[-keep_each:]}"


# Initialize logging when module is imported
setup_logging()

