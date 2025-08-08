from modules.api.base import ApiJobSite
from pprint import pprint as pp

class GreenhouseApiSite(ApiJobSite):
    def scrape(self):
        print(f"Scraping Greenhouse API site: {self.name}")
        self.method = "GET"
        data = super().scrape()
    
        if not data:
            return None
        
        if 'jobs' not in data:
            print(f"No jobs found for {self.name}.")
            return None
        
        jobs = self.transform(data["jobs"])
        
        return jobs
    
    def transform(self, data):
        jobs = []
        for item in data:
            remote = False
            hybrid = False
            salary = item.get("salary", {})
            if isinstance(salary, dict):
                min_salary = salary.get("minValue")
                max_salary = salary.get("maxValue")
            else:
                min_salary = None
                max_salary = None

            location_city = None
            location_state = None
            location_country = None
            location_obj = item.get("location", {})
            location = location_obj.get("name", None)
            try:
                # TODO - need to check against list of actual countries and or states to parse inconsistent location strings
                if "," in location:
                    location_data = location.split(",")
                    location_country = location_data[-1].strip() if len(location_data) > 0 else None
                    location_state = location_data[-2].strip() if len(location_data) > 2 else None
                    location_city = location_data[0].strip() if len(location_data) > 1 else None
                else:
                    location_city = location

                remote = True if "remote" in location.lower() else False
                hybrid = True if "hybrid" in location.lower() else False
            except:
                # no location data
                pass


            job = {
                "site_id": self.id,
                "source_url": self.url,
                "job_id": item.get("internal_job_id"),
                "title": item.get("title"),
                "company_name": item.get("company_name"),
                "apply_url": item.get("absolute_url"),
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