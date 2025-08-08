import time 
import requests
from bs4 import BeautifulSoup
from modules.bsoup.base import BsoupJobSite
from pprint import pprint as pp
from urllib.parse import urlparse, parse_qs, urljoin

class VentureLoopJobSite(BsoupJobSite):

    def scrape(self):
        
        data = []

        # this avoids endless loops for unpredictable reason

        for page in range (0, 100):
            current_url = f"{self.url}/pagination.php?&p={page}"
            current_url = current_url.replace("//pagination","/pagination")
            #print(f"Fetching page {page}: {current_url}")

            try:
                response = requests.get(current_url)
                if response.status_code != 200:
                    print(f"Failed to fetch page {page} with status code {response.status_code}")
                    break
            except Exception as e:
                print(f"Exception occurred while fetching page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Find all job elements; adjust the class name if necessary.
            job_elements = soup.find_all(class_="jobs_row")
            if not job_elements:
                #print("No job elements found; end of pagination.")
                break

            #print(f"Found {len(job_elements)} job elements on page {page}")
            for idx, elem in enumerate(job_elements):
                try:
                    location = None
                    remote = False
                    # Using similar CSS selectors as in the Selenium example.
                    title_elem = elem.select_one("div.jobs_topRow > div.jobs_descriptionBx > div.job_text > h3")
                    title = title_elem.get_text(strip=True) if title_elem else None 
                    if not title:
                        print(f"No title found for job element on page {page}, index {idx}. Skipping.")
                        continue
                    link_elem = elem.select_one("div.jobs_btnnRow > div.apply_btnbx > div > div > a")
                    link = link_elem["href"] if link_elem and link_elem.has_attr("href") else None

                    remainder_elem = elem.select_one("div.jobs_topRow > div.jobs_descriptionBx > div.job_text > h4")
                    remainder_text = remainder_elem.get_text(strip=False) if remainder_elem else None 

                    company_elem = elem.select_one("div.jobs_topRow > div.jobs_descriptionBx > div.job_text > h4 > span")
                    company = company_elem.get_text(strip=False) if company_elem else None
                    if remainder_text and company:
                        remainder_text = remainder_text.replace(company, "")
                        if "remote" in remainder_text.lower():
                            remote = True
                            remainder_text = remainder_text.replace("Remote", "").replace("remote", "")
                        # split be line break
                        lines = remainder_text.split("\n")
                        
                        location = lines[0]
                    company = company.replace("-", "").strip() if company else None

                    record = {
                        "id": f"{page}-{idx}",
                        "title": title,
                        "company_name": company,
                        "apply_url": link,
                        "location": location,
                        "remote": remote,
                    }
                    data.append(record)
                    #pp(record)
                except Exception as e:
                    print(f"Error parsing a job element on page {page}: {e}")
           
                
        jobs = self.transform(data)
        return jobs
    
    def transform(self, data):
        jobs = []
        for item in data:
          
            location_city = None
            location_state = None
            location_country = None

            try: 
                if "," in  item['location']:
                    # TODO - need to check against list of actual countries and or states to parse inconsistent location strings
                    location_data = item['location'].split(",")
                    location_country = location_data[-1].strip() if len(location_data) > 0 else None
                    location_state = location_data[-2].strip() if len(location_data) > 2 else None
                    location_city = location_data[0].strip() if len(location_data) > 1 else None
                else:
                    location_city = item['location']
            except Exception as e:
                print(f"Error parsing location data: {e}")
                pass

            apply_url = item.get("apply_url", "")
            if apply_url:
                # Convert the relative URL to a full URL.
                full_apply_url = urljoin(self.url, apply_url)
                # Parse the URL to extract the job id from the query parameters.
                parsed_url = urlparse(full_apply_url)
                job_id = parse_qs(parsed_url.query).get("jobid", [None])[0]
            else:
                job_id = item.get("id", None)
                full_apply_url = None

            job = {
                "site_id": self.id,
                "source_url": self.url,
                "job_id": job_id,
                "title": item.get("title"),
                "company_name": item.get("company_name"),
                "apply_url": full_apply_url,
                "min_salary": None,
                "max_salary": None,
                "location_city": location_city,
                "location_state": location_state,
                "location_country": location_country,
                "remote": item.get("remote", False),
                "hybrid": False,
            }
            #pp(job)
            jobs.append(job)

        return jobs