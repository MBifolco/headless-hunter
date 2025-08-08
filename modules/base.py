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
        
        if not self.location_check(job):
            return False

        if not self.position_check(job):
            return False
        
        if not self.remote_check(job) and not self.location_check(job):
            print(f"Job {job['title']} does not match remote or location criteria.")
            print(f"Job location: {job.get('location_city', '')}, Remote: {job.get('remote', False)}")
            return False
        
        return True
    
    def location_check(self, job):
        location_city = job.get("location_city", None)
        if not location_city:
            return True

        location_terms = self.app_config.get("location_terms", [])
    
        if any(term.lower() in location_city.lower() for term in location_terms):
            return True
    
        return False
    
    def remote_check(self, job):
        remote = job.get("remote", False)
        remote_preference = self.app_config.get("remote", False)

        if remote and remote_preference:
            return True
        return False
    

    def position_check(self, job):
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