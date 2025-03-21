import requests
import json
import sqlite3
import time
import difflib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

DATABASE_NAME = "jobs.db"

# ====================
# Application Config
# ====================
APP_CONFIG = {
    "positive_terms": ["vp of product", "head of product", "chief product officer", "director of product", "product manager"],
    "negative_terms": [],
    "threshold": 0.9  # Fuzzy match threshold (0 to 1)
}

def should_save_job(job, app_config):
    """
    Determines if a job should be saved based on fuzzy matching of the job title.
    Returns a tuple: (should_save (bool), best_score (float)).
    A job is saved if at least one positive term's fuzzy match score on the job title
    exceeds the threshold and none of the negative terms appear in the title.
    """
    title = job.get("title", "").lower()
    positive_terms = app_config.get("positive_terms", [])
    negative_terms = app_config.get("negative_terms", [])
    threshold = app_config.get("threshold", 0.7)
    
    # Check for any negative term present exactly in the title.
    for neg in negative_terms:
        if neg.lower() in title:
            #print(f"Skipping job '{title}' due to negative term match: '{neg}'")
            return False, 0.0

    # Compute fuzzy matching scores for each positive term.
    best_score = 0.0
    for pos in positive_terms:
        ratio = difflib.SequenceMatcher(None, title, pos.lower()).ratio()
        if ratio > best_score:
            best_score = ratio

    if best_score >= threshold:
        return True, best_score
    else:
        #print(f"Skipping job '{title}' as it does not match any positive term sufficiently (best score: {best_score:.2f}).")
        return False, best_score

# ====================
# Database Functions
# ====================

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

# ====================
# OOP Scraper Classes
# ====================

class JobSite:
    """Base class for all job sites."""
    def __init__(self, id, name, url, **kwargs):
        self.id = id
        self.name = name
        self.url = url
        self.config = kwargs

    def scrape(self):
        """Subclasses must override this method to implement scraping."""
        raise NotImplementedError("Subclasses must implement scrape()")

class ApiJobSite(JobSite):
    """Intermediate class for API-based sites."""
    def __init__(self, id, name, url, method="GET", payload=None, **kwargs):
        super().__init__(id, name, url, **kwargs)
        self.method = method.upper()
        self.payload = payload or {}

    def scrape(self):
        try:
            print(f"Scraping API site {self.name} using {self.method}")
            if self.method == "POST":
                response = requests.post(self.url, json=self.payload)
            else:
                response = requests.get(self.url, params=self.payload)
            
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Error scraping API site {self.name}: {e}")
            return None

class SeleniumJobSite(JobSite):
    """Intermediate class for Selenium-based sites."""
    def __init__(self, id, name, url, **kwargs):
        super().__init__(id, name, url, **kwargs)

    def scrape(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)
        try:
            print(f"Scraping Selenium site {self.name}")
            self.driver.get(self.url)
            time.sleep(5)
            # Default behavior: return the page source.
            return self.driver.page_source
        except Exception as e:
            print(f"Error scraping Selenium site {self.name}: {e}")
            return None
        finally:
            self.driver.quit()
    
    def try_click(self, element, how=None, what=None, show_error=False):
        click_target = element
        if how is not None and what is not None:
            try:
                click_target = element.find_element(how, what)
            except Exception as e:
                print('error finding element',  what, e)
                return False
       
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(click_target).perform()
            click_target.click()
            return True
        except Exception as e:
            if show_error:
                print('error clicking element', how, what, e)
            return False
        return False
    
    def load_more(self, how, what):
        clicked = self.try_click(self.driver, how, what)
        if clicked:
            time.sleep(3)
            self.load_more(how, what)
        
    def scroll_to_bottom(self):
        # Get initial scroll height.
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll to the bottom.
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait for new content to load.
            time.sleep(2)
            # Calculate new scroll height and compare with last height.
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If heights are the same, we've reached the end.
                break
            last_height = new_height

# Specific child for Consider API sites (e.g. andreessen-horowitz, sequoia-capital)
class ConsiderApiSite(ApiJobSite):
    def scrape(self):
        print(f"Scraping Consider API site: {self.name}")
        self.method = "POST"
        self.payload = {
            "meta": {"size": 1000},
            "board": {"id": self.id, "isParent": True},
            "query": {"promoteFeatured": True}
        }
        print(self.payload)
        data = super().scrape()
        # Assumes the API returns JSON with a key "jobs"
        return data

# Specific child for Getro Selenium site (e.g. 2150)
class GetroSeleniumSite(SeleniumJobSite):
    def scrape(self):
        print(f"Scraping Getro Selenium site: {self.name}")
        options = Options()
        #options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)

        try:
            print(f"Scraping Getro Selenium site {self.name} {self.url}")
            self.driver.get(self.url)
            time.sleep(5)
            self.load_more(By.XPATH, "//button[normalize-space()='Load more']")
            self.scroll_to_bottom()
            jobs = []
            # Update these selectors based on the actual HTML structure of the site.
            job_elements = self.driver.find_elements(By.CLASS_NAME, "job-info")
            if not job_elements:
                print("No job elements found; please update the selector for site 2150.")
            for idx, elem in enumerate(job_elements):
                try:
                    title_elem = elem.find_element(By.CSS_SELECTOR, "h4 > a > div > div")
                    title = title_elem.text.strip()
                    link_elem = elem.find_element(By.CSS_SELECTOR, "h4 > a")
                    link = link_elem.get_attribute("href")
                    company_elem = elem.find_element(By.CSS_SELECTOR, "div > div:nth-child(1) > a")
                    company = company_elem.text.strip()
                    location_elem = elem.find_element(By.CSS_SELECTOR, "div > div:nth-child(2) > div:nth-child(1) > div > div > div > span")
                    location = location_elem.text.strip()
                    # Create a simple job object.
                    job = {
                        "jobId": f"{self.name}-{idx}",
                        "title": title,
                        "companyName": company,
                        "companyId": company,
                        "companyDomain": "",
                        "applyUrl": link,
                        "url": link,
                        "timeStamp": "",
                        "salary": {},
                        "minYearsExp": None,
                        "remote": False,
                        "hybrid": False,
                        "isFeatured": False
                    }
                    print(f"Found job: {title} - {link} {location }")
                    jobs.append(job)
                except Exception as e:
                    print(f"Error parsing a job element on {self.name}: {e}")
            return {"jobs": jobs}
        except Exception as e:
            print(f"Error scraping Getro Selenium site {self.name}: {e}")
            return None
        finally:
            self.driver.quit()

# ====================
# Mapping and Config
# ====================

# Map the 'type' field from the config to the corresponding scraper class.
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
CONFIG = [
    
    {
        "id": "andreessen-horowitz",
        "name": "Andreessen Horowitz",
        "type": "consider",
        "url": "https://jobs.a16z.com/api-boards/search-jobs"
    },
    {
        "id": "sequoia-capital",
        "name": "Sequoia Capital",
        "type": "consider",
        "url": "https://jobs.sequoiacap.com/api-boards/search-jobs"
    },
    {
        "id": "1517-fund",
        "name": "1517 Fund",
        "type": "consider",
        "url": "https://jobs.1517fund.com/api-boards/search-jobs"
    },
]

# ====================
# Main Processing
# ====================

def main():
    conn = create_db()
    
    for site_config in CONFIG:
        # Pop the 'type' field to determine which scraper class to use.
        site_id = site_config.get("id")
        site_type = site_config.pop("type")
        site_name = site_config.get("name")
        scraper_class = SCRAPER_CLASSES.get(site_type)
        if not scraper_class:
            print(f"No scraper class defined for type '{site_type}' (site: {site_name}). Skipping.")
            continue
        
        # Instantiate the appropriate scraper using the config.
        scraper = scraper_class(**site_config)
        data = scraper.scrape()
        if data is not None:
            jobs = data.get("jobs", [])
            if jobs:
                print(f"Found {len(jobs)} jobs for {site_name}.")
                for job in jobs:
                    match, score = should_save_job(job, APP_CONFIG)
                    if match:
                        job["fuzzyScore"] = score
                        save_job(conn, job)
                    #else:
                    #    print(f"Job {job.get('jobId')} did not meet search criteria. Skipping.")
            else:
                print(f"No jobs found for {site_name}.")
        else:
            print(f"Failed to scrape data from {site_name}.")
    
    # Query and output the total count of jobs in the database.
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    print(f"Total number of jobs in the database: {count}")
    conn.close()
    print("Finished processing all sites.")

if __name__ == "__main__":
    main()
