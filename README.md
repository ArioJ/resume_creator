
# Resume Advisor Platform

AI-powered resume analysis and optimization platform that helps job seekers improve their resumes by comparing them against target job descriptions using OpenAI GPT-4.

## What this platform does

- **Upload Resume**: Accepts resume files (PDF, DOCX, TXT) and extracts text
- **Analyze Against Job Description**: Compares your resume with a job description using AI
- **9-Dimensional Evaluation**: Scores your resume across 9 key dimensions
- **Identify Skills**: Finds overlapping skills and gaps between your resume and the job
- **Generate Insights**: Provides detailed analysis and actionable recommendations
- **PDF Report**: Creates a professional downloadable PDF report
- **Interactive Dashboard**: Displays results with charts and detailed breakdowns

Supported file formats: `.pdf`, `.docx`, `.txt` (max 10MB)

## Project layout

- `main.py` - Main FastAPI application with routing and static file serving
- `endpoints/` - API endpoint modules (upload, analyze, generate report)
- `utils/` - Core utilities (OpenAI client, resume analyzer, scoring engine, PDF generator)
- `frontend/` - HTML, CSS, and JavaScript for the web interface
- `data/` - Storage for extracted resume text and analysis results
- `reports/` - Generated PDF reports
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (OpenAI API key) - **YOU MUST CONFIGURE THIS**

## Create & activate a virtual environment (recommended)

The following commands show how to create and activate a virtual environment for this project.

PowerShell (Windows) - recommended for this workspace:

```powershell
python -m venv .venv
# If you see an execution policy error when activating, run PowerShell as Administrator and allow RemoteSigned or run: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Command Prompt (cmd.exe):

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

macOS / Linux (bash/zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation you should see the virtualenv name (for example `.venv`) in your prompt.

## Install dependencies

With the virtual environment activated, install the required packages:

```powershell
python -m pip install -r requirements.txt
```

## Configure OpenAI API Key

**IMPORTANT**: Before running the server, ensure your `.env` file contains your OpenAI API key:

```
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
MAX_TOKENS=4000
TEMPERATURE=0.3
```

If you don't have an OpenAI API key, get one at: https://platform.openai.com/api-keys

## Run the server

Start the FastAPI app locally using Uvicorn (development mode / auto-reload):

```powershell
uvicorn main:app --reload
```

The web interface will be available at `http://127.0.0.1:8000`

The OpenAPI docs will be available at `http://127.0.0.1:8000/docs`

## How to Use

1. **Open your browser** and go to `http://127.0.0.1:8000`

2. **Upload your resume** (PDF, DOCX, or TXT format)

3. **Paste the job description** you're targeting (minimum 50 characters)

4. **Click "Start Analysis"** and wait 30-60 seconds while the AI analyzes your resume

5. **View your results** on the interactive dashboard:
   - Overall fit score
   - Overlapping skills
   - Skill gaps with importance levels
   - Detailed scores across 9 dimensions
   - Actionable recommendations

6. **Download PDF report** for a professional summary of the analysis

## Evaluation Dimensions

Your resume is evaluated across 9 key dimensions:

1. **Relevance of Experience** - How well your experience matches the role
2. **Impact and Achievements** - Demonstrated accomplishments and results
3. **Technical Proficiency** - Match of technical skills required
4. **Clarity and Structure** - Resume formatting and organization
5. **Quantifiable Results** - Use of metrics and measurable outcomes
6. **Communication and Writing Quality** - Professional writing quality
7. **Growth and Progression** - Career trajectory and advancement
8. **Innovation and Problem-Solving** - Creative solutions and initiatives
9. **ATS Compatibility** - Optimization for applicant tracking systems

## API Endpoints

### POST /api/upload-resume
Upload resume file for text extraction
- Accepts: PDF, DOCX, TXT (multipart/form-data)
- Returns: `{ "resume_id": "<uuid>", "filename": "...", "num_chars": <n> }`

### POST /api/analyze
Analyze resume against job description
- Body: `{ "resume_id": "<uuid>", "job_description": "..." }`
- Returns: Complete analysis with scores, skills, gaps, and recommendations

### GET /api/analysis/{analysis_id}
Retrieve previously completed analysis

### POST /api/generate-report/{analysis_id}
Generate PDF report for an analysis

### GET /api/download-report/{report_id}
Download generated PDF report

### GET /health
Health check endpoint

### Example: Using the API Directly (PowerShell)

```powershell
# 1. Upload resume
$resp = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/upload-resume -Method Post -Form @{ file = Get-Item './my_resume.pdf' }
$resumeId = $resp.resume_id

# 2. Analyze resume
$analysisResp = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/analyze -Method Post -ContentType "application/json" -Body (@{
    resume_id = $resumeId
    job_description = "Your job description text here..."
} | ConvertTo-Json)

$analysisId = $analysisResp.analysis_id

# 3. Generate and download report
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/generate-report/$analysisId" -Method Post
Start-Process "http://127.0.0.1:8000/api/download-report/$analysisId"
```

## How It Works

1. **Text Extraction**: Uses `PyPDF2`, `docx2txt` to extract text from resumes
2. **AI Analysis**: Leverages OpenAI GPT-4 Turbo for intelligent evaluation
3. **Skill Matching**: AI identifies overlapping skills and gaps
4. **Dimensional Scoring**: Each dimension evaluated with specific prompts and criteria
5. **Report Generation**: Professional PDFs created with ReportLab
6. **Interactive UI**: Modern responsive design with Chart.js for visualizations

## Limits and Considerations

- **Upload size**: Limited to 10 MB per file
- **File types**: Only PDF, DOCX, and TXT are supported
- **Job description**: Minimum 50 characters required
- **Analysis time**: Typically 30-60 seconds (depends on resume/job description length)
- **Cost**: Each analysis uses OpenAI API tokens (~$0.15-$0.30 per analysis)
- **Storage**: Analysis results stored locally in `data/analysis/`
- **No authentication**: Designed for personal local use

## Technology Stack

- **Backend**: Python, FastAPI, Uvicorn
- **AI/ML**: OpenAI GPT-4 Turbo API
- **PDF Processing**: PyPDF2, docx2txt
- **PDF Generation**: ReportLab
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Visualization**: Chart.js
- **Environment**: python-dotenv

## Troubleshooting

### PowerShell Execution Policy
If PowerShell refuses to activate the venv, run:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### OpenAI API Errors
- Verify your API key in `.env` file is correct
- Check your OpenAI account has available credits
- Ensure you haven't exceeded rate limits

### File Upload Issues
- Ensure file is under 10MB
- Check file format is PDF, DOCX, or TXT
- For PDF files, ensure text is extractable (not scanned images)

### Missing Dependencies
If you see import errors, reinstall dependencies:
```powershell
python -m pip install -r requirements.txt --force-reinstall
```

### Port Already in Use
If port 8000 is busy, run on a different port:
```powershell
uvicorn main:app --reload --port 8001
```

## Cost Estimation

Each analysis typically uses:
- 15,000-20,000 OpenAI tokens
- Approximate cost: $0.15-$0.30 per analysis
- Cost varies based on resume and job description length

Monitor your usage at: https://platform.openai.com/usage

## Future Enhancements

Potential features for future versions:
- User authentication and analysis history
- Resume template library
- Side-by-side comparison of multiple resumes
- LinkedIn profile integration
- Batch processing for recruiters
- Multi-language support
- Custom evaluation dimensions

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review FastAPI docs at `/docs` endpoint
3. Check OpenAI API status
4. Review server logs for detailed error messages