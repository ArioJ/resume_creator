# Quick Start - PostgreSQL Database

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start PostgreSQL
```bash
# Option A: Docker (Easiest)
docker run --name resume_advisor_db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=resume_advisor \
  -p 5432:5432 \
  -d postgres:15

# Option B: Local PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql     # Linux
```

### 3. Create .env File
```bash
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_advisor" > .env
echo "OPENAI_API_KEY=your_key_here" >> .env
```

### 4. Initialize Database
```bash
python init_db.py
# Type 'no' when asked to reset
```

### 5. Start Application
```bash
uvicorn main:app --reload
```

### 6. Test
Visit: http://localhost:8000

---

## 📊 Common Database Commands

### View Data
```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/resume_advisor

# View all resumes
SELECT id, filename, created_at FROM resumes ORDER BY created_at DESC;

# View all analyses with scores
SELECT id, overall_score, created_at FROM analyses ORDER BY created_at DESC;

# View complete workflow
SELECT 
    r.filename as resume,
    a.overall_score as score,
    o.id as has_optimized,
    rep.id as has_report
FROM resumes r
LEFT JOIN analyses a ON r.id = a.resume_id
LEFT JOIN optimized_resumes o ON a.id = o.analysis_id
LEFT JOIN reports rep ON a.id = rep.analysis_id
ORDER BY r.created_at DESC;

# Exit
\q
```

### Cleanup
```bash
# Reset database (WARNING: Deletes all data)
python init_db.py
# Type 'yes' and then 'RESET' to confirm

# Or manually
psql postgresql://postgres:postgres@localhost:5432/resume_advisor
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
\q
python init_db.py
```

### Stop PostgreSQL
```bash
# Docker
docker stop resume_advisor_db

# macOS
brew services stop postgresql@15

# Linux
sudo systemctl stop postgresql
```

---

## 🔧 Troubleshooting

### "Connection refused"
```bash
# Check if PostgreSQL is running
docker ps                                    # Docker
brew services list                           # macOS
sudo systemctl status postgresql             # Linux
```

### "Database does not exist"
```bash
psql postgres -c "CREATE DATABASE resume_advisor;"
```

### "Authentication failed"
Check your `.env` file - ensure credentials match PostgreSQL setup

---

## 📚 Full Documentation
- Detailed setup: `DATABASE_SETUP.md`
- Implementation details: `docs/DATABASE_MIGRATION_COMPLETE.md`


