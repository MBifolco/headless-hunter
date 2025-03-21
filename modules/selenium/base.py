from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from modules.base import JobSite

class SeleniumJobSite(JobSite):
    """Intermediate class for Selenium-based sites."""
    def __init__(self, id, name, url, **kwargs):
        super().__init__(id, name, url, **kwargs)

    def scrape(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)
        try:
            print(f"Scraping Selenium site {self.name}")
            self.driver.get(self.url)
            time.sleep(5)
            # Default behavior: return the page source.
            return self.driver.page_source
        except Exception as e:
            print(f"Error scraping Selenium site {self.name}: {e}")
            return None
        finally:
            self.driver.quit()
    
    def try_click(self, element, how=None, what=None, show_error=False):
        click_target = element
        if how is not None and what is not None:
            try:
                click_target = element.find_element(how, what)
            except Exception as e:
                print('error finding element',  what, e)
                return False
       
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(click_target).perform()
            click_target.click()
            return True
        except Exception as e:
            if show_error:
                print('error clicking element', how, what, e)
            return False
        return False
    
    def load_more(self, how, what):
        clicked = self.try_click(self.driver, how, what)
        if clicked:
            time.sleep(3)
            self.load_more(how, what)
        
    def scroll_to_bottom(self):
        # Get initial scroll height.
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll to the bottom.
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait for new content to load.
            time.sleep(2)
            # Calculate new scroll height and compare with last height.
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If heights are the same, we've reached the end.
                break
            last_height = new_height