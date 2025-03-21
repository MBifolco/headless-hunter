# headless-hunter
Run headless-hunter on your local machine to automate a job-search.  

Headless-hunter was created to make it easy to do two things:
1. Ensure your search covers as many jobs as possible from the companies/sites you care about
2. Allow for better/custom filtering of those jobs

## Setup
1. Update the positive keyword list in main.py to accurately reflect the types of job titles you want.
2. Update the negative keyword list in main.py to exclude certain titles (Optional)
3. Update the fuzzy matching threshold to suit your needs

## Run
Run `search.py`

## See Results
Run `app.py` open up http://localhost:8000

## Adding More Sites
If there is a site you'd like to search add it to site_configs.json.  Currently HH only supports sites using Consider or Getro to power their listings, however, you can add another module for the site yourself.
