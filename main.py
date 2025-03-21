import difflib
import json
import os
import requests
import sqlite3
import time

from dotenv import load_dotenv
from modules.db import create_db, save_job
from modules.api.consider import ConsiderApiSite
from modules.selenium.getro import GetroSeleniumSite

# Load environment variables from a local .env file
load_dotenv()

APP_CONFIG = {
    "positive_terms": ["vp of product", "head of product", "chief product officer", "director of product", "product manager"],
    "negative_terms": [],
    "threshold": 0.9  # Fuzzy match threshold (0 to 1)
}

SCRAPER_CLASSES = {
    "consider": ConsiderApiSite,
    "getro": GetroSeleniumSite,
}
"""
{
        "id": "2150",
        "name": "2150",
        "type": "getro",
        "url": "https://2150.getro.com/jobs"
    },
"""
# Configuration for job sites.
# load sites.json from file
with open('site_configs.json') as f:
    SITE_CONFIGS = json.load(f)

# ====================
# Main Processing
# ====================
def main():
    conn = create_db()
    
    for site_config in SITE_CONFIGS:
        site_id = site_config.get("id")
        site_type = site_config.pop("type")
        site_name = site_config.get("name")
        scraper_class = SCRAPER_CLASSES.get(site_type)
        if not scraper_class:
            print(f"No scraper class defined for type '{site_type}' (site: {site_name}). Skipping.")
            continue
        
        scraper = scraper_class(app_config = APP_CONFIG, **site_config)
    
        data = scraper.scrape()
        if data is not None:
            jobs = data.get("jobs", [])
            if jobs:
                print(f"Found {len(jobs)} jobs for {site_name}.")
                for job in jobs:
                    match, score = scraper.should_save_job(job)
                    if match:
                        job["fuzzyScore"] = score
                        save_job(conn, job)
            else:
                print(f"No jobs found for {site_name}.")
        else:
            print(f"Failed to scrape data from {site_name}.")
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    summary = f"Job Scraper Summary:\n\nTotal number of jobs in the database: {count}"
    print(summary)
    
    conn.close()

if __name__ == "__main__":
    main()
