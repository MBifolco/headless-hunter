from modules.api.base import ApiJobSite
from pprint import pprint as pp

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
        if not data:
            return None
        jobs = self.transform(data["jobs"])
        return jobs
    
    def transform(self, data):
        jobs = []
        for item in data:
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
            locations = item.get("locations", {})
            try:
                # TODO - need to check against list of actual countries and or states to parse inconsistent location strings
                if "," in locations[0]:
                    location_data = locations[0].split(",")
                    location_country = location_data[-1].strip() if len(location_data) > 0 else None
                    location_state = location_data[-2].strip() if len(location_data) > 2 else None
                    location_city = location_data[0].strip() if len(location_data) > 1 else None
                else:
                    location_city = locations[0]

                if "remote" in locations[0].lower():
                    remote = True
                if "hybrid" in locations[0].lower():
                    hybrid = True
            except:
                # no location data
                pass

            remote = item.get("remote", False)
            if not remote and "remote" in item.get("title", "").lower():
                remote = True
            hybrid = item.get("hybrid", False)
            if not hybrid and "hybrid" in item.get("title", "").lower():
                hybrid = True

            job = {
                "site_id": self.id,
                "source_url": self.url,
                "job_id": item.get("jobId"),
                "title": item.get("title"),
                "company_name": item.get("companyName"),
                "apply_url": item.get("applyUrl"),
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