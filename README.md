# headless-hunter
Run headless-hunter on your local machine to automate a job-search.  

Headless-hunter was created to make it easy to do two things:
1. Ensure your search covers as many jobs as possible from the companies/sites you care about
2. Allow for better/custom filtering of those jobs

## Job Scraping
### Setup
1. Update the positive keyword list in main.py to accurately reflect the types of job titles you want.
2. Update the negative keyword list in main.py to exclude certain titles (Optional)

### Run
Run `search.py`

### See Results
Run `app.py` open up http://localhost:8000

### Adding More Sites
Currently HH supports automated scraping of any sites using the following job listing services:

- Consider
- Getro 
- Greenhouse
- Workday
- Ventureloop

To add a site that uses one of the above - just add it to the site_configs.json file. 

You can add another module yourself for any site or service - if you do please create a PR so we can add it to the repo.

## Automated Career Page Searching
We have a script that given a list of urls can do a few things:

### Default Functionality
1. Provide a csv of career page urls
2. Run `python find_listings.py` 
#### What it does: 
- For each page it will attempt to determine if the it is powered by one of the providers listed above (Consider, Getro, etc) 
- Save the results to a csv.

### Crawling Functionality
1. Provide a csv of domains (or really any non-career page url)
2. Run `python find_listings.py` provide one of the following arguments `--crawl` and/or `--portfolio`
#### What it does (crawl only): 
- On each url provided it will look for links that might go to a career or job listing 
- Follow them
- Run the default functionality on it.
#### What it does (portfolio): 
- Runs the crawl function
- If nothing is found it will look for links that might go to a portfolio of companies
- Follow them
- Runs the craw function again on portfolio page

### Other Arguments
- `--output` can set the name of the csv to which the results are saved