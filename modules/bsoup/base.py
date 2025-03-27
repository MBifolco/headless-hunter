import time 

from modules.base import JobSite

class BsoupJobSite(JobSite):
    """Intermediate class for Selenium-based sites."""
    def __init__(self, id, name, url, **kwargs):
        super().__init__(id, name, url, **kwargs)

