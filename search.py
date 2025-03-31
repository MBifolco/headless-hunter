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
from modules.api.greenhouse import GreenhouseApiSite
from modules.bsoup.ventureloop import VentureLoopJobSite
from pprint import pprint as pp

# Load environment variables from a local .env file
load_dotenv()

APP_CONFIG = {
    "positive_terms": ["vp of product", "head of product", "chief product officer"],
    "negative_terms": ["Product Design", "Product Marketing", "Product Development", "Product Engineering", "Product Operations", "Product Insights", "Production", "Product Compliance", "Product Analytics", "Product Ops"],
    "location_terms" : ["new york", "ny","USA","United States","US","NYC"],
    "remote" : True,
}

SCRAPER_CLASSES = {
    "consider": ConsiderApiSite,
    "getro": GetroSeleniumSite,
    "greenhouse": GreenhouseApiSite,
    "ventureloop": VentureLoopJobSite,
}


SITE_CONFIGS = []

CONFIG_FILES = [
    'ventureloop_sites.json',
    'consider_sites.json',
    'greenhouse_sites.json',
    'getro_sites.json',
]
#CONFIG_FILES = ['test_site_configs.json']

for config_file in CONFIG_FILES:
    if os.path.exists(config_file):
        with open(config_file) as f:
            SITE_CONFIGS.extend(json.load(f))
    else:
        print(f"Config file {config_file} does not exist. Skipping.")



# ====================
# Main Processing
# ====================
def main():
    conn = create_db()
    total_jobs_checked = 0
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
            total_jobs_checked += len(jobs)
            print(f"Found {len(jobs)} jobs for {site_name}. Total jobs checked: {total_jobs_checked}")
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
