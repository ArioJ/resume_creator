# Resume Advisor Platform - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Activate Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web server)
- OpenAI (AI analysis)
- ReportLab (PDF generation)
- PyPDF2, docx2txt (file processing)
- python-dotenv (environment variables)
- tiktoken (token counting)

### Step 3: Verify Your .env File

Make sure your `.env` file exists and contains:

```
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
MAX_TOKENS=4000
TEMPERATURE=0.3
```

### Step 4: Start the Server

```powershell
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Step 5: Open the Application

Open your web browser and navigate to:
```
http://127.0.0.1:8000
```

## 📝 How to Use

### Basic Workflow

1. **Upload Resume**
   - Click the upload area or drag & drop your resume
   - Supported formats: PDF, DOCX, TXT (max 10MB)
   - Click "Next: Job Description"

2. **Enter Job Description**
   - Paste the complete job description (minimum 50 characters)
   - Include requirements, responsibilities, and qualifications
   - Click "Next: Analyze"

3. **Start Analysis**
   - Review the preview
   - Click "Start Analysis"
   - Wait 30-60 seconds for AI processing

4. **View Results**
   - See your overall fit score (0-100)
   - Explore 9 dimension scores
   - Review overlapping skills and gaps
   - Read detailed recommendations

5. **Download Report**
   - Click "Download PDF Report"
   - Professional PDF will be generated
   - Save for your records or share with career advisors

## 🎯 Sample Job Description for Testing

If you want to test the platform quickly, use this sample job description:

```
Senior Software Engineer

We're seeking a talented Senior Software Engineer to join our dynamic team. 

Requirements:
- 5+ years of professional software development experience
- Strong proficiency in Python, JavaScript, and SQL
- Experience with FastAPI or similar web frameworks
- Knowledge of cloud platforms (AWS, Azure, or GCP)
- Excellent problem-solving and communication skills
- Experience with Agile methodologies

Responsibilities:
- Design and implement scalable web applications
- Collaborate with cross-functional teams
- Mentor junior developers
- Participate in code reviews
- Contribute to technical documentation
- Drive innovation and continuous improvement

Preferred Qualifications:
- Bachelor's degree in Computer Science or related field
- Experience with Docker and Kubernetes
- Knowledge of CI/CD pipelines
- Open source contributions
- Leadership experience
```

## 📊 Understanding Your Results

### Overall Score Interpretation

- **80-100**: Excellent fit - Resume strongly matches the job
- **60-79**: Good fit - Some areas for improvement
- **40-59**: Moderate fit - Significant gaps to address
- **0-39**: Poor fit - Major improvements needed

### The 9 Dimensions

1. **Relevance of Experience** (20% weight)
   - How well your work history matches the role
   
2. **Impact and Achievements** (15% weight)
   - Your demonstrated accomplishments
   
3. **Technical Proficiency** (15% weight)
   - Match of required technical skills
   
4. **Clarity and Structure** (10% weight)
   - Resume format and readability
   
5. **Quantifiable Results** (10% weight)
   - Use of numbers and metrics
   
6. **Communication and Writing Quality** (8% weight)
   - Professional language and clarity
   
7. **Growth and Progression** (8% weight)
   - Career advancement pattern
   
8. **Innovation and Problem-Solving** (9% weight)
   - Creative solutions demonstrated
   
9. **ATS Compatibility** (5% weight)
   - Optimization for applicant tracking systems

### Skills Analysis

**Overlapping Skills** (Green Badges)
- Skills found in both your resume and the job description
- These are your strengths - highlight them!

**Skill Gaps** (Red Cards with Priority Levels)
- **HIGH**: Critical skills missing - address immediately
- **MEDIUM**: Important but not critical - work on these
- **LOW**: Nice-to-have skills - consider if relevant

## 🔧 Troubleshooting

### "OpenAI API call failed"
- Check your API key in `.env`
- Verify you have credits: https://platform.openai.com/usage
- Check rate limits haven't been exceeded

### "Resume not found"
- Ensure Step 1 (upload) completed successfully
- Check server logs for upload errors
- Try uploading again

### "No extractable text found"
- For PDFs: Ensure text is selectable (not a scanned image)
- Try converting to DOCX or TXT format
- Check file isn't corrupted

### Server Won't Start
```powershell
# Kill any process using port 8000
netstat -ano | findstr :8000
# Then use a different port
uvicorn main:app --reload --port 8001
```

### Missing Dependencies
```powershell
# Reinstall everything
python -m pip install -r requirements.txt --force-reinstall
```

## 💰 Cost Management

Each analysis costs approximately **$0.15-$0.30** in OpenAI API credits.

To minimize costs:
- Don't analyze the same resume multiple times unnecessarily
- Keep job descriptions focused and relevant
- Monitor your usage at: https://platform.openai.com/usage
- Set spending limits in your OpenAI account

## 🎨 Features Overview

### Frontend Features
- ✅ Drag & drop file upload
- ✅ Multi-step form with validation
- ✅ Real-time character counting
- ✅ Loading indicators
- ✅ Interactive radar chart
- ✅ Tabbed navigation
- ✅ Color-coded scores
- ✅ Responsive mobile design

### Backend Features
- ✅ Resume text extraction (PDF, DOCX, TXT)
- ✅ OpenAI GPT-4 integration
- ✅ 9-dimensional analysis
- ✅ Skills matching and gap identification
- ✅ Professional PDF report generation
- ✅ RESTful API endpoints
- ✅ Error handling and logging

## 📁 File Storage

The platform stores files locally:

- **data/**: Uploaded resume texts
- **data/analysis/**: Analysis results (JSON)
- **reports/**: Generated PDF reports

These files persist until you delete them. No cloud storage is used.

## 🔒 Privacy & Security

- ✅ All processing happens locally on your machine
- ✅ Resume data sent to OpenAI for analysis (encrypted in transit)
- ✅ No user accounts or authentication required
- ✅ No data shared with third parties (except OpenAI for processing)
- ✅ You can delete all stored files at any time

## 📚 API Documentation

While the web interface is the primary way to use the platform, the API is fully documented:

**Interactive API Docs**: http://127.0.0.1:8000/docs

Key endpoints:
- `POST /api/upload-resume` - Upload resume file
- `POST /api/analyze` - Analyze resume vs job description
- `POST /api/generate-report/{analysis_id}` - Generate PDF
- `GET /api/download-report/{report_id}` - Download PDF

## 🎓 Tips for Best Results

### Resume Tips
1. **Use a clean format**: Avoid complex layouts, tables, or graphics
2. **Include keywords**: Match terminology from the job description
3. **Quantify achievements**: Use numbers, percentages, and metrics
4. **Be specific**: Name technologies, tools, and methodologies
5. **Show progression**: Highlight career growth and increased responsibility

### Job Description Tips
1. **Include the full description**: Don't truncate or summarize
2. **Include requirements section**: Technical and soft skills
3. **Include responsibilities**: Day-to-day activities
4. **Include qualifications**: Education, experience, certifications
5. **Include company context**: Industry, team size, etc. if available

### Analysis Tips
1. **Review all dimensions**: Don't just focus on the overall score
2. **Prioritize high-impact gaps**: Focus on HIGH priority missing skills
3. **Read recommendations carefully**: Actionable advice for improvement
4. **Use the PDF report**: Share with mentors or career advisors
5. **Iterate**: Make changes and re-analyze to track improvement

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Server logs appear in your terminal
2. **Check the browser console**: Press F12 in your browser
3. **Review the README**: Comprehensive documentation available
4. **Test with sample data**: Use the sample job description above
5. **Verify your environment**: API key, dependencies, ports

## 🚀 Next Steps

After your first analysis:

1. **Review your results carefully**
2. **Update your resume based on recommendations**
3. **Run analysis again to see improvement**
4. **Test with different job descriptions**
5. **Keep your most successful analyses for reference**

---

**Ready to optimize your resume? Let's get started!** 🎉

