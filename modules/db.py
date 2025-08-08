import sqlite3
import json
import os
import datetime
from uuid import uuid4
# Use environment variable for database name, or default to "jobs.db"
DATABASE_NAME = os.environ.get("DATABASE_NAME", "jobs.db")

def create_db():
    """Creates the SQLite database and the 'jobs' table if it doesn't already exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            site_id TEXT,
            job_id TEXT,
            title TEXT,
            company_name TEXT,
            apply_url TEXT,
            source_url TEXT,
            salary_min REAL,
            salary_max REAL,
            location_city TEXT,
            location_state TEXT,
            location_country TEXT,
            remote BOOLEAN,
            hybrid BOOLEAN,
            last_seen DATE,
            status TEXT DEFAULT '',
            UNIQUE(site_id, job_id)
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

    site_id = job.get("site_id")
    job_id = job.get("job_id")
    title = job.get("title")
    company_name = job.get("company_name")
    apply_url = job.get("apply_url")
    source_url = job.get("source_url")
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    location_city = job.get("location_city")
    location_state = job.get("location_state")
    location_country = job.get("location_country")
    remote = int(job.get("remote", False))
    hybrid = int(job.get("hybrid", False))
    last_seen = datetime.datetime.now().strftime("%Y-%m-%d")

    print(site_id, job_id, title, company_name, apply_url, source_url, salary_min, salary_max, location_city, location_state, location_country, remote, hybrid, last_seen, last_seen)
    try:
        cursor.execute('''
            INSERT INTO jobs 
            (id, site_id, job_id, title, company_name, apply_url, source_url, salary_min, salary_max, location_city, location_state, location_country, remote, hybrid, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
            ON CONFLICT(site_id, job_id) DO UPDATE SET last_seen = ?
        ''',(str(uuid4()), site_id, job_id, title, company_name, apply_url, source_url, salary_min, salary_max, location_city, location_state, location_country, remote, hybrid, last_seen, last_seen))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Saved job: {job_id} - {title}")
        else:
            print(f"Job {job_id} - {title} already exists. Skipping.")
    except Exception as e:
        print(f"Error saving job {job_id}: {e}")

def update_job(conn, job, scrape_batch):
    # updates date for job
    cursor = conn.cursor()
    job_id = job.get("jobId")
    last_seen = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute('''
            UPDATE jobs 
            SET last_seen = ?
            WHERE job_id = ?
        ''', (scrape_batch, job_id))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Updated job: {job_id}")
        else:
            print(f"Job {job_id} not found for update. Skipping.")
    except Exception as e:
        print(f"Error updating job {job_id}: {e}")


def update_table(conn):
    """
    Updates the 'jobs' table to add a new column if it doesn't already exist.
    This is useful for adding new fields to the job records without losing existing data.
    """
    cursor = conn.cursor()
    try:
        cursor.execute('''
            ALTER TABLE jobs ADD COLUMN status TEXT DEFAULT ''
        ''')
        conn.commit()
        print("Table updated successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column already exists. No changes made.")
        else:
            print(f"Error updating table: {e}")