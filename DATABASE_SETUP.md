# PostgreSQL Database Setup Guide

This guide will help you set up and use the PostgreSQL database for the Resume Advisor Platform.

## 📋 Prerequisites

- PostgreSQL 12+ installed on your system
- Python 3.8+
- Virtual environment activated

## 🚀 Quick Start

### 1. Install PostgreSQL Dependencies

```bash
# Activate your virtual environment first
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

#### Option A: Local PostgreSQL Installation

**Install PostgreSQL:**
- **macOS**: `brew install postgresql@15`
- **Ubuntu**: `sudo apt-get install postgresql postgresql-contrib`
- **Windows**: Download from https://www.postgresql.org/download/

**Start PostgreSQL:**
```bash
# macOS (Homebrew)
brew services start postgresql@15

# Ubuntu
sudo systemctl start postgresql

# Windows - PostgreSQL runs as a service automatically
```

**Create Database:**
```bash
# Connect to PostgreSQL
psql postgres

# In PostgreSQL shell:
CREATE DATABASE resume_advisor;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE resume_advisor TO postgres;
\q
```

#### Option B: Using Docker (Recommended for Development)

```bash
# Run PostgreSQL in Docker
docker run --name resume_advisor_db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=resume_advisor \
  -p 5432:5432 \
  -d postgres:15

# Check if it's running
docker ps
```

### 3. Configure Database Connection

Create a `.env` file in the project root (copy from `database_config.example`):

```bash
# Copy the example file
cp database_config.example .env
```

Edit `.env` with your database credentials:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_advisor
OPENAI_API_KEY=your_openai_api_key_here
```

**Connection String Format:**
```
postgresql://[username]:[password]@[host]:[port]/[database_name]
```

### 4. Initialize Database Tables

Run the initialization script:

```bash
python init_db.py
```

You should see output like:
```
🗄️  RESUME ADVISOR - DATABASE INITIALIZATION
1. Testing database connection...
✓ Database connection successful

2. Database initialization options:
   - Create tables (if they don't exist)
   - Reset database (drop all tables and recreate)

Do you want to RESET the database? (yes/no) [no]: no

3. Creating database tables...
✓ Database tables created successfully!

✅ Database initialization successful!

You can now start the application with: uvicorn main:app --reload
```

## 📊 Database Schema

The database consists of 4 main tables:

### 1. **resumes**
Stores uploaded resume content
- `id` (UUID, Primary Key)
- `filename` (VARCHAR)
- `content` (TEXT)
- `file_size_bytes` (INTEGER)
- `created_at` (TIMESTAMP)

### 2. **analyses**
Stores analysis results for resume-job pairs
- `id` (UUID, Primary Key)
- `resume_id` (UUID, Foreign Key → resumes)
- `job_description` (TEXT)
- `overall_score` (INTEGER)
- `results_json` (TEXT) - Complete analysis results
- `created_at` (TIMESTAMP)

### 3. **optimized_resumes**
Stores AI-generated optimized resumes
- `id` (UUID, Primary Key)
- `analysis_id` (UUID, Foreign Key → analyses)
- `content` (TEXT)
- `format` (VARCHAR) - Default: 'markdown'
- `created_at` (TIMESTAMP)

### 4. **reports**
Tracks generated PDF reports
- `id` (UUID, Primary Key)
- `analysis_id` (UUID, Foreign Key → analyses)
- `file_path` (VARCHAR)
- `report_type` (VARCHAR) - 'analysis' or 'optimized_resume'
- `created_at` (TIMESTAMP)

## 🔧 Database Management

### View Database Tables

```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/resume_advisor

# List all tables
\dt

# Describe a table
\d resumes
\d analyses
\d optimized_resumes
\d reports

# View data
SELECT id, filename, created_at FROM resumes;
SELECT id, overall_score, created_at FROM analyses;

# Exit
\q
```

### Reset Database

```bash
python init_db.py
# When prompted, type 'yes' and then 'RESET' to confirm
```

### Backup Database

```bash
# Create backup
pg_dump -U postgres -d resume_advisor > backup.sql

# Restore from backup
psql -U postgres -d resume_advisor < backup.sql
```

## 🧪 Testing the Setup

### 1. Start the Application

```bash
uvicorn main:app --reload
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Test Database Connection

Visit http://127.0.0.1:8000/health

Expected response:
```json
{
  "status": "healthy",
  "service": "Resume Advisor Platform"
}
```

### 3. Test Complete Workflow

1. **Upload Resume**: Open http://127.0.0.1:8000/ and upload a resume
2. **Add Job Description**: Paste a job description
3. **Analyze**: Click "Analyze Resume"
4. **Check Database**: 

```bash
psql postgresql://postgres:postgres@localhost:5432/resume_advisor

SELECT COUNT(*) FROM resumes;
SELECT COUNT(*) FROM analyses;
```

## 🔍 Troubleshooting

### Connection Refused

**Error**: `could not connect to server: Connection refused`

**Solutions**:
1. Check if PostgreSQL is running:
   ```bash
   # macOS
   brew services list
   
   # Ubuntu
   sudo systemctl status postgresql
   
   # Docker
   docker ps
   ```

2. Verify port 5432 is not in use:
   ```bash
   lsof -i :5432  # macOS/Linux
   netstat -an | find "5432"  # Windows
   ```

### Authentication Failed

**Error**: `FATAL: password authentication failed for user "postgres"`

**Solutions**:
1. Double-check your `.env` file credentials
2. Verify user exists:
   ```bash
   psql postgres -c "SELECT usename FROM pg_user;"
   ```

### Database Does Not Exist

**Error**: `FATAL: database "resume_advisor" does not exist`

**Solution**:
```bash
psql postgres -c "CREATE DATABASE resume_advisor;"
```

### Import Error: No module named 'psycopg2'

**Solution**:
```bash
pip install psycopg2-binary
```

## 📈 Performance Tips

1. **Connection Pooling**: Already configured with `pool_size=5, max_overflow=10`
2. **Indexes**: Consider adding indexes for frequently queried fields:
   ```sql
   CREATE INDEX idx_analyses_resume_id ON analyses(resume_id);
   CREATE INDEX idx_optimized_resumes_analysis_id ON optimized_resumes(analysis_id);
   ```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use strong passwords** in production
3. **Restrict database user permissions** in production
4. **Enable SSL** for production database connections:
   ```python
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```

## 🚀 Production Deployment

For production, consider:

1. **Managed PostgreSQL**:
   - AWS RDS
   - Google Cloud SQL
   - Heroku Postgres
   - DigitalOcean Managed Databases

2. **Environment Variables**:
   Set `DATABASE_URL` in your hosting platform's environment variables

3. **Migration Strategy**:
   - Keep file-based backups during transition
   - Test thoroughly before going live
   - Plan for rollback if needed

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Database Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)

## ✅ Migration Checklist

- [x] PostgreSQL installed and running
- [x] Database created
- [x] Dependencies installed
- [x] `.env` file configured
- [x] Database tables initialized
- [x] Application starts without errors
- [x] Upload resume test passes
- [x] Analysis test passes
- [x] Data visible in database

---

**Need Help?** Check the logs in `app_log/` directory for detailed error messages.


