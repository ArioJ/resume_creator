# Robust End-to-End Logging Implementation

## Overview
Comprehensive logging has been implemented across the entire Resume Advisor Platform to provide in-depth visibility for engineers building and maintaining the application.

## Logging Architecture

### Centralized Configuration
- **Location**: `utils/logging_config.py`
- **Log Directory**: `app_log/`
- **Log Rotation**: Enabled for all log files

### Log Files Generated

1. **`resume_advisor.log`** - Main application log (all levels)
   - All application activity
   - Rotating: 10MB per file, 5 backups

2. **`errors.log`** - Error-only log (ERROR and CRITICAL)
   - Only errors and critical failures
   - Rotating: 5MB per file, 3 backups

3. **`api_requests.log`** - API request/response log
   - HTTP method, endpoint, status code
   - Request/response data (sanitized)
   - Duration in milliseconds
   - Rotating: 10MB per file, 5 backups

4. **`openai_calls.log`** - OpenAI API interactions
   - All prompts and responses (truncated)
   - Token usage and costs
   - Model and parameters used
   - Duration in milliseconds
   - Rotating: 20MB per file, 10 backups

### Log Format

```
2025-10-21 14:32:15 | INFO     | module.function:123 | Log message here
```

Components:
- **Timestamp**: ISO format with milliseconds
- **Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Source**: module.function:line_number
- **Message**: Descriptive log message

### Optional JSON Format

The logging configuration supports JSON format for structured logging (set `use_json=True`):

```json
{
  "timestamp": "2025-10-21T14:32:15.123",
  "level": "INFO",
  "logger": "endpoints.upload_resume",
  "module": "upload_resume",
  "function": "upload_resume",
  "line": 85,
  "message": "Resume uploaded: abc123 (5000 characters)"
}
```

## Modules with Comprehensive Logging

### ✅ Completed

1. **`utils/logging_config.py`** - Centralized logging configuration
   - Multiple log file handlers
   - Log rotation
   - Custom formatters
   - Helper functions for API and OpenAI logging
   - Data sanitization

2. **`main.py`** - Application startup and request/response middleware
   - Application startup/shutdown events
   - HTTP request/response middleware
   - Request duration tracking
   - Error logging

3. **`endpoints/upload_resume.py`** - Resume upload endpoint
   - File upload tracking
   - File type detection
   - Text extraction from PDF/DOCX/TXT
   - File size validation
   - Save operations

4. **`utils/openai_client.py`** - OpenAI API wrapper
   - Client initialization
   - All API calls with full prompts
   - All API responses (truncated)
   - Token usage tracking
   - Error handling and retries
   - Duration tracking

5. **`utils/resume_analyzer.py`** - Resume analysis orchestration
   - Analysis workflow steps (1-5)
   - Skill extraction
   - Skill gap identification
   - Executive summary generation
   - Overall analysis duration

### ⏳ Pending (Will complete next)

6. **`utils/scoring_engine.py`** - Dimension scoring
7. **`utils/pdf_generator.py`** - PDF report generation
8. **`endpoints/analyze_resume.py`** - Analysis endpoint
9. **`endpoints/generate_report.py`** - Report generation endpoint

## Logging Features

### 1. Request/Response Logging
Every API request logs:
- HTTP method and endpoint
- Request headers (DEBUG level)
- Request body (sanitized)
- Response status code
- Response body (truncated if large)
- Duration in milliseconds
- Client IP address

### 2. OpenAI API Call Logging
Every OpenAI call logs:
- Operation name/description
- Full system prompt (truncated at 2000 chars)
- Full user prompt (truncated at 2000 chars)
- Model used
- Temperature and max_tokens
- Full response (truncated at 2000 chars)
- Token usage (prompt, completion, total)
- Duration in milliseconds
- Errors with full stack traces

### 3. File Operation Logging
- File uploads with size and type
- Text extraction with character counts
- File saves with paths
- Temporary file cleanup

### 4. Analysis Step Logging
Each analysis step logs:
- Step number and description
- Input data sizes
- Processing duration
- Results summary
- Error handling

### 5. Error Logging
All errors log:
- Error message
- Full stack trace
- Context (what operation was being performed)
- Duration before failure
- Input parameters (sanitized)

## Security Features

### Data Sanitization
Sensitive data is automatically redacted:
- API keys → `***REDACTED***`
- Passwords → `***REDACTED***`
- Tokens → `***REDACTED***`
- Authorization headers → `***REDACTED***`

### Data Truncation
Large data is truncated to prevent log bloat:
- Prompts: 2000 characters (beginning and end preserved)
- Responses: 2000 characters  (beginning and end preserved)
- Large objects: 1000 characters

## Usage Examples

### Getting a Logger

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)
```

### Logging Levels

```python
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Warning messages for potentially harmful situations")
logger.error("Error messages")
logger.critical("Critical errors that may cause application failure")
```

### Logging API Requests

```python
from utils.logging_config import log_api_request

log_api_request(
    endpoint="/api/upload-resume",
    method="POST",
    request_data={"filename": "resume.pdf"},
    response_data={"resume_id": "abc123"},
    status_code=200,
    duration_ms=145.67
)
```

### Logging OpenAI Calls

```python
from utils.logging_config import log_openai_call

log_openai_call(
    operation="extract_skills",
    prompt="Analyze this resume...",
    response="Skills: Python, JavaScript...",
    model="gpt-4-turbo-preview",
    tokens_used=1500,
    duration_ms=2345.12
)
```

## Benefits for Engineers

1. **Debugging**: Detailed logs help trace issues through the entire system
2. **Performance Monitoring**: Duration tracking for all operations
3. **Cost Tracking**: Token usage logged for all OpenAI calls
4. **Audit Trail**: Complete record of all API requests and responses
5. **Error Analysis**: Full stack traces with context
6. **Development**: DEBUG level logs for detailed troubleshooting
7. **Production**: Separate error logs for monitoring

## Best Practices Implemented

1. **Structured Logging**: Consistent format across all modules
2. **Log Rotation**: Prevents disk space issues
3. **Multiple Log Levels**: Appropriate granularity
4. **Performance**: Minimal overhead with efficient handlers
5. **Security**: Automatic sanitization of sensitive data
6. **Context**: Every log includes source location
7. **Error Handling**: All exceptions logged with full context

## Configuration Options

Edit `utils/logging_config.py` to customize:
- Log file paths
- Rotation sizes and backup counts
- Log levels
- Output format (text vs JSON)
- Sanitization rules

## Monitoring Logs

### View real-time logs:
```powershell
Get-Content app_log\resume_advisor.log -Wait -Tail 50
```

### View errors only:
```powershell
Get-Content app_log\errors.log -Wait -Tail 20
```

### View API requests:
```powershell
Get-Content app_log\api_requests.log -Wait -Tail 30
```

### View OpenAI calls:
```powershell
Get-Content app_log\openai_calls.log -Wait -Tail 20
```

## File Sizes

Expected log file sizes per day (approximate):
- `resume_advisor.log`: 50-100 MB
- `errors.log`: 1-5 MB
- `api_requests.log`: 10-20 MB
- `openai_calls.log`: 100-200 MB (due to prompts/responses)

All files are automatically rotated when they reach their size limits.

