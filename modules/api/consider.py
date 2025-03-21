from modules.api.base import ApiJobSite

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