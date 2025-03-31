import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from modules.selenium.base import SeleniumJobSite
from pprint import pprint as pp

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
            data = []
            # Update these selectors based on the actual HTML structure of the site.
            job_elements = self.driver.find_elements(By.CLASS_NAME, "job-info")
            if not job_elements:
                print("No job elements found; please update the selector for site 2150.")

                
            for idx, elem in enumerate(job_elements):
                try:
                    title = self.return_text_if_exists(elem, By.CSS_SELECTOR, "h4 > a > div > div")
                    link_elem = self.return_element_if_exists(elem, By.CSS_SELECTOR, "h4 > a")
                    link = link_elem.get_attribute("href") if link_elem else None
                    company = self.return_text_if_exists(elem, By.CSS_SELECTOR, "div > div:nth-child(1) > a")
                    location = self.return_text_if_exists(elem, By.CSS_SELECTOR, "div > div:nth-child(2) > div:nth-child(1) > div > div > div > span")
                    salary = self.return_text_if_exists(elem, By.CSS_SELECTOR, "div > div:nth-child(2) > div:nth-child(2) > p")
                        
                    # Create a simple job object.
                    record = {
                        "id": idx,
                        "title": title,
                        "company_name": company,
                        "apply_url": link,
                        "location": location,
                        "salary": salary,
                    }
                    #print(f"Found job: {title} - {link} {location }")
                    data.append(record)
                except Exception as e:
                    print(f"Error parsing a job element on {self.name}")
           
            jobs = self.transform(data)
            return jobs
        except Exception as e:
            print(f"Error scraping Getro Selenium site {self.name}: {e}")
            return None
        finally:
            self.driver.quit()

    def transform(self, data):
        jobs = []
        for item in data:
          
            location_city = None
            location_state = None
            location_country = None
            remote = False
            hybrid = False
            min_salary = None
            max_salary = None
            if item.get("location", ""):
                try: 
                    if item['location'].lower() == 'remote':
                        remote = True
                    elif item['location'].lower() == 'hybrid':
                        hybrid = True
                    elif "," in  item['location']:
                        # TODO - need to check against list of actual countries and or states to parse inconsistent location strings
                        location_data = item['location'].split(",")
                        location_country = location_data[-1].strip() if len(location_data) > 0 else None
                        location_state = location_data[-2].strip() if len(location_data) > 2 else None
                        location_city = location_data[0].strip() if len(location_data) > 1 else None
                    else:
                        location_city = item['location']
                except Exception as e:
                    pp(item)
                    print(f"Error parsing location data: {e}")
                    pass

            if "hybrid" in item.get("title", "").lower():
                hybrid = True

            if "remote" in item.get("title", "").lower():
                remote = True

            if item.get("salary", ""):
                salary = item.get("salary", "").replace("$", "").replace("k","").replace("USD", "").strip()
                if "/" in salary:
                    salary = salary.split("/")[0]
                if "-" in salary:
                    min_salary, max_salary = salary.split("-")

            apply_url = item.get("apply_url", "")
            if apply_url:
                job_page = apply_url.split("/")[-1]
                job_id = job_page.split("-")[0]
            else:
                job_id = item.get("id", None)

            job = {
                "site_id": self.id,
                "source_url": self.url,
                "job_id": job_id,
                "title": item.get("title"),
                "company_name": item.get("company_name"),
                "apply_url": apply_url,
                "min_salary": min_salary,
                "max_salary": max_salary,
                "location_city": location_city,
                "location_state": location_state,
                "location_country": location_country,
                "remote": remote,
                "hybrid": hybrid,
            }
        
            jobs.append(job)

        return jobs