# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Headless Hunter is a Python-based job scraping automation tool designed to search and filter job listings from various company career pages. The project uses multiple scraping strategies (APIs, Selenium, BeautifulSoup) to extract job data from different job board providers.

## Key Commands

### Running the Application
- **Main job scraper**: `python search.py`
- **Web interface**: `python app.py` (serves on http://localhost:8000)
- **Career page finder**: `python find_listings.py` (with optional `--crawl` and `--portfolio` flags)
- **Install dependencies**: `pip install -r requirements.txt`
- **Run tests**: `pytest` or `pytest tests/`
- **Run specific test**: `pytest tests/test_modules_base.py::TestClassName::test_method_name`

## Architecture

### Core Components

1. **Job Scraping System** (`search.py`)
   - Orchestrates scraping from multiple job board providers
   - Uses configuration files (*_sites.json) to define sites to scrape
   - Applies filtering based on positive/negative keywords, location, and remote preferences
   - Stores results in SQLite database (jobs.db)

2. **Scraper Modules** (`modules/`)
   - **Base Class**: `modules/base.py` - JobSite abstract class with filtering logic
   - **API Scrapers**: 
     - `modules/api/consider.py` - Consider.com API integration
     - `modules/api/greenhouse.py` - Greenhouse.io API integration
   - **Selenium Scrapers**:
     - `modules/selenium/getro.py` - Getro site scraping using Selenium
   - **BeautifulSoup Scrapers**:
     - `modules/bsoup/ventureloop.py` - VentureLoop scraping
   - **Database**: `modules/db.py` - SQLite database management

3. **Web Interface** (`app.py`)
   - FastAPI application for viewing and managing scraped jobs
   - Allows updating job status (e.g., marking as reviewed)
   - Template in `templates/index.html`

4. **Career Page Discovery** (`find_listings.py`)
   - Discovers career pages from a list of company URLs
   - Identifies job board provider (Consider, Getro, Greenhouse, VentureLoop, Workday)
   - Can crawl sites looking for career/job links
   - Can follow portfolio/investment links for VC sites

### Configuration Files

- **Site Configurations**: JSON files defining sites to scrape
  - `consider_sites.json` - Consider.com powered sites
  - `getro_sites.json` - Getro powered sites
  - `greenhouse_sites.json` - Greenhouse.io powered sites
  - `ventureloop_sites.json` - VentureLoop powered sites
- **Input Files**:
  - `urls.csv` - Input for find_listings.py (column header: "urls")
- **Output Files**:
  - `career_links.csv` - Output from find_listings.py
  - `jobs.db` - SQLite database with scraped jobs

### Filtering Configuration

Set in `APP_CONFIG` in search.py:
- `positive_terms`: Job titles to include
- `negative_terms`: Keywords to exclude from titles
- `location_terms`: Acceptable locations
- `remote`: Whether to include remote positions

## Database Schema

The SQLite database (`jobs.db`) stores job listings with fields including:
- job_id, title, company_name, apply_url
- location_city, location_state, location_country
- remote, hybrid flags
- last_seen timestamp
- site_id (source site identifier)
- status (for tracking application status)

## Environment Variables

- `DATABASE_NAME`: SQLite database filename (default: "jobs.db")
- Uses `.env` file for configuration (loaded via python-dotenv)

## Testing

Tests are located in the `tests/` directory. The project uses pytest for testing.
Configuration is in `pytest.ini` which specifies the test directory and file pattern.