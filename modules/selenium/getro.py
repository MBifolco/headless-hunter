from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from modules.selenium.base import SeleniumJobSite

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
