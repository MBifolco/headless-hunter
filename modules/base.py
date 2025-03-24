import difflib


class JobSite:
    """Base class for all job sites."""
    def __init__(self, id, name, url, app_config, **kwargs):
        self.id = id
        self.name = name
        self.url = url
        self.config = kwargs
        self.app_config = app_config

    def scrape(self):
        """Subclasses must override this method to implement scraping."""
        raise NotImplementedError("Subclasses must implement scrape()")
    
    def should_save_job(self, job):
        title = job.get("title", "").lower()
        positive_terms = self.app_config.get("positive_terms", [])
        negative_terms = self.app_config.get("negative_terms", [])
        
        # Check for any negative term present exactly in the title.
        for neg in negative_terms:
            if neg.lower() in title:
                return False
        
        # Check for any positive term exactly in the title.
        for pos in positive_terms:
            if pos.lower() in title:
                return True

        return False
    
    def transform(self, data):
        # Placeholder for any transformation logic if needed
        return data