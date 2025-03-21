import sqlite3
import json
import os


# Use environment variable for database name, or default to "jobs.db"
DATABASE_NAME = os.environ.get("DATABASE_NAME", "jobs.db")

def create_db():
    """Creates the SQLite database and the 'jobs' table if it doesn't already exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company_name TEXT,
            company_id TEXT,
            company_domain TEXT,
            apply_url TEXT,
            url TEXT,
            timeStamp TEXT,
            salary_min REAL,
            salary_max REAL,
            min_years_exp INTEGER,
            remote BOOLEAN,
            hybrid BOOLEAN,
            is_featured BOOLEAN,
            fuzzy_score REAL,
            raw_data TEXT
        )
    ''')
    conn.commit()
    return conn

def save_job(conn, job):
    """
    Saves a single job record into the SQLite database.
    Only adds a job if it doesn't already exist.
    Selected fields are extracted from the job object, and the entire job is stored as JSON.
    """
    cursor = conn.cursor()
    job_id = job.get("jobId")
    title = job.get("title")
    company_name = job.get("companyName")
    company_id = job.get("companyId")
    company_domain = job.get("companyDomain")
    apply_url = job.get("applyUrl")
    url = job.get("url")
    timeStamp = job.get("timeStamp")
    salary = job.get("salary", {})
    salary_min = salary.get("minValue")
    salary_max = salary.get("maxValue")
    min_years_exp = job.get("minYearsExp")
    remote = int(job.get("remote", False))
    hybrid = int(job.get("hybrid", False))
    is_featured = int(job.get("isFeatured", False))
    fuzzy_score = job.get("fuzzyScore")
    raw_data = json.dumps(job)
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO jobs 
            (job_id, title, company_name, company_id, company_domain, apply_url, url, timeStamp, salary_min, salary_max, min_years_exp, remote, hybrid, is_featured, fuzzy_score, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, title, company_name, company_id, company_domain, apply_url, url, timeStamp, salary_min, salary_max, min_years_exp, remote, hybrid, is_featured, fuzzy_score, raw_data))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Saved job: {job_id} - {title} (fuzzy score: {fuzzy_score:.2f})")
        else:
            print(f"Job {job_id} - {title} already exists. Skipping.")
    except Exception as e:
        print(f"Error saving job {job_id}: {e}")