import requests

from modules.base import JobSite

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