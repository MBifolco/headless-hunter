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
from pprint import pprint as pp

# Load environment variables from a local .env file
load_dotenv()

APP_CONFIG = {
    "positive_terms": ["vp of product", "head of product", "chief product officer"],
    "negative_terms": ["Product Design", "Product Marketing", "Product Development", "Product Engineering", "Product Operations", "Product Insights", "Production", "Product Compliance", "Product Analytics", "Product Ops"],
    "threshold": 0.8  # Fuzzy match threshold (0 to 1)
}

SCRAPER_CLASSES = {
    "consider": ConsiderApiSite,
    "getro": GetroSeleniumSite,
}


SITE_CONFIGS = []
"""
#load test configs
with open('test_site_configs.json') as f:
    SITE_CONFIGS.extend(json.load(f))
"""
#load consider configs
with open('consider_sites.json') as f:
    SITE_CONFIGS.extend(json.load(f))
# load sites.json from file
with open('getro_sites.json') as f:
    SITE_CONFIGS.extend(json.load(f))

# ====================
# Main Processing
# ====================
def main():
    conn = create_db()
    
    for site_config in SITE_CONFIGS:
        site_type = site_config.pop("type")
        site_name = site_config.get("name")
        scraper_class = SCRAPER_CLASSES.get(site_type)
        if not scraper_class:
            print(f"No scraper class defined for type '{site_type}' (site: {site_name}). Skipping.")
            continue
        
        #if site_type == "consider":
        #    continue
        scraper = scraper_class(app_config = APP_CONFIG, **site_config)
    
        jobs = scraper.scrape()
    
        if jobs is not None:
            print(f"Found {len(jobs)} jobs for {site_name}.")
            saved = 0
            for job in jobs:
                if scraper.should_save_job(job):
                    saved += 1
                    save_job(conn, job)
            print(f"Saved {saved} jobs for {site_name}.")
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
