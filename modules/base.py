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
        """
        Determines if a job should be saved based on fuzzy matching of the job title.
        Returns a tuple: (should_save (bool), best_score (float)).
        A job is saved if at least one positive term's fuzzy match score on the job title
        exceeds the threshold and none of the negative terms appear in the title.
        """
        title = job.get("title", "").lower()
        positive_terms = self.app_config.get("positive_terms", [])
        negative_terms = self.app_config.get("negative_terms", [])
        threshold = self.app_config.get("threshold", 0.7)
        
        # Check for any negative term present exactly in the title.
        for neg in negative_terms:
            if neg.lower() in title:
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
            return False, best_score