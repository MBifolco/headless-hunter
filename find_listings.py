import os
import json
import time
import pandas as pd
from urllib.parse import urlparse

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

RESULTS_FILE = "career_links.json"

def extract_domain(url):
    """Extract domain from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path
    except:
        return ""

def contains_keyword(text, keywords):
    """Return True if the text contains any of the keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

def find_career_links(driver):
    """
    Search for <a> elements that indicate career/job pages by:
    1. Checking if visible text contains career-related keywords
    2. Checking if the URL itself contains career-related keywords
    Returns a list of target URLs.
    """
    elements = driver.find_elements(By.XPATH, "//a")
    career_links = []
    career_keywords = ["careers", "jobs", "career", "job board", "job openings", "job list", "job opportunities", "hiring", "join", "work"]
    url_keywords = ["career", "job", "hiring", "work", "join", "opportunity", "opening", "position", "recruit", "talent", "employ"]
    
    for element in elements:
        try:
            href = element.get_attribute("href")
            if not href:
                continue
                
            # Check if we've already found this URL
            if href in career_links:
                continue
            
            # Check 1: Element text contains career keywords
            element_text = element.text
            if element_text and contains_keyword(element_text, career_keywords):
                career_links.append(href)
                continue
            
            # Check 2: URL itself contains career keywords (including subdomains)
            href_lower = href.lower()
            
            # Check for career-related subdomains (e.g., careers.example.com, jobs.example.com)
            try:
                parsed = urlparse(href_lower)
                hostname = parsed.netloc
                # Check if subdomain contains career keywords
                subdomain_keywords = ["career", "job", "hiring", "recruit", "talent", "employ", "work", "join"]
                if any(keyword in hostname for keyword in subdomain_keywords):
                    career_links.append(href)
                    continue
            except:
                pass
            
            # Check for keywords in the full URL
            if any(keyword in href_lower for keyword in url_keywords):
                # Additional check: avoid false positives from blog posts about jobs
                avoid_patterns = ["/blog/", "/news/", "/article/", "/post/", "/press/"]
                if not any(pattern in href_lower for pattern in avoid_patterns):
                    career_links.append(href)
                    continue
            
            # Check 3: Common career page URL patterns
            common_patterns = ["/careers", "/jobs", "/join-us", "/join-our-team", "/work-with-us", 
                             "/opportunities", "/openings", "/positions", "/hiring", "/recruit",
                             "/talent", "/employment", "/apply"]
            if any(pattern in href_lower for pattern in common_patterns):
                career_links.append(href)
                
        except Exception:
            continue
    
    return career_links

def get_portfolio_investment_links(driver):
    """
    Retrieve URLs from any <a> or <button> elements whose visible text contains "portfolio" or "investments".
    Only returns elements with a valid href attribute.
    """
    elements = driver.find_elements(By.XPATH, "//a | //button")
    links = []
    for element in elements:
        try:
            if element.text and contains_keyword(element.text, ["portfolio", "investments"]):
                href = element.get_attribute("href")
                if href and href not in links:
                    links.append(href)
        except Exception:
            continue
    return links

def get_powered_by_info(driver):
    """
    Check the current page for job board systems.
    Returns a tuple (powered_by, api_id) where powered_by is the system name or an empty string.
    """
    powered_by = ""
    api_id = ""
    page_source = driver.page_source
    current_url = str(driver.current_url)

    print(f"  Checking powered-by for: {current_url}")

    if "Powered by Consider" in page_source:
        powered_by = "consider"
        try:
            # Find the div with class "boards-body"
            element = driver.find_element(By.CSS_SELECTOR, "div.boards-body")
            class_attr = element.get_attribute("class")
            classes = class_attr.split()
            # Exclude the base class to extract the id from the other class
            other_classes = [cls for cls in classes if cls != "boards-body"]
            if other_classes:
                api_id = other_classes[0]
        except Exception:
            pass
    elif "Powered by Getro" in page_source:
        powered_by = "getro"
    elif "boards.greenhouse.io" in page_source or "greenhouse.io" in current_url:
        powered_by = "greenhouse"
        # Try to extract the company ID from greenhouse URLs
        try:
            for link in driver.find_elements(By.XPATH, "//a"):
                href = link.get_attribute("href")
                if href and "boards.greenhouse.io" in href:
                    split_url = href.split("/")
                    if len(split_url) > 3:
                        api_id = split_url[3]
                        break
        except:
            pass
    elif "myworkdayjobs.com" in current_url:
        powered_by = "workday"
        try:
            split_url = current_url.split("/")
            api_id = split_url[2].split(".")[0]
        except:
            pass
    elif "VentureLoop" in page_source:
        powered_by = "ventureloop"
    elif "lever.co" in current_url or "jobs.lever.co" in current_url:
        powered_by = "lever"
        try:
            # Extract company from lever URL like jobs.lever.co/company
            parsed = urlparse(current_url)
            if "lever.co" in parsed.netloc:
                path_parts = parsed.path.strip("/").split("/")
                if path_parts and path_parts[0]:
                    api_id = path_parts[0]
        except:
            pass
    elif "ashbyhq.com" in current_url or "jobs.ashbyhq.com" in current_url:
        powered_by = "ashby"
    elif "bamboohr.com" in current_url:
        powered_by = "bamboohr"
    elif "recruitee.com" in current_url:
        powered_by = "recruitee"
    elif "breezy.hr" in current_url or "breezyjobs" in page_source:
        powered_by = "breezy"
    elif "workable.com" in current_url or "apply.workable.com" in current_url:
        powered_by = "workable"

    return powered_by, api_id

def process_career_page(driver, career_url, timeout=10):
    """
    Navigate to a career URL and determine what powers it.
    Returns a dict with career_url, powered_by, and api_id.
    """
    result = {
        "url": career_url,
        "powered_by": "",
        "api_id": ""
    }
    
    if career_url:
        try:
            # Set page load timeout
            driver.set_page_load_timeout(timeout)
            driver.get(career_url)
            time.sleep(2)  # Allow the career page to load
            powered_by, api_id = get_powered_by_info(driver)
            result["powered_by"] = powered_by
            result["api_id"] = api_id
        except TimeoutException:
            print(f"    Timeout loading career page (>{timeout}s): {career_url}")
        except WebDriverException as e:
            if "timeout" in str(e).lower():
                print(f"    Page load timeout: {career_url}")
            else:
                print(f"    WebDriver error: {career_url}: {str(e)[:100]}")
        except Exception as e:
            print(f"    Error processing career link {career_url}: {str(e)[:100]}")
    
    return result

def process_url(driver, url, crawl=False, portfolio=False, timeout=15):
    """
    Process a single URL and return all career pages found.
    Returns a dict with original_url, domain, and career_pages.
    """
    # Ensure URL has http/https
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    
    result = {
        "original_url": url,
        "domain": extract_domain(url),
        "career_pages": {}
    }
    
    print(f"\nProcessing: {url}")
    
    try:
        if crawl:
            # Try to find career/job links on the page
            try:
                driver.set_page_load_timeout(timeout)
                driver.get(url)
                time.sleep(2)
            except TimeoutException:
                print(f"  Timeout loading main page (>{timeout}s), skipping...")
                return result
            except WebDriverException as e:
                if "timeout" in str(e).lower():
                    print(f"  Page load timeout, skipping...")
                else:
                    print(f"  WebDriver error loading page: {str(e)[:100]}")
                return result
            
            print("  Searching for career/job links...")
            career_links = find_career_links(driver)
            
            if career_links:
                print(f"  Found {len(career_links)} career link(s)")
                for career_link in career_links:
                    if career_link and career_link != url:  # Avoid processing the same URL
                        career_info = process_career_page(driver, career_link)
                        # Use the career URL as the key
                        result["career_pages"][career_link] = {
                            "powered_by": career_info["powered_by"],
                            "api_id": career_info["api_id"]
                        }
            
            # If no career links found and portfolio flag is set, check portfolio links
            if not career_links and portfolio:
                print("  No career links found, checking portfolio/investment links...")
                portfolio_links = get_portfolio_investment_links(driver)
                
                for p_link in portfolio_links:
                    print(f"  Following portfolio link: {p_link}")
                    try:
                        driver.set_page_load_timeout(timeout)
                        driver.get(p_link)
                        time.sleep(2)
                        
                        # Search for career links on the portfolio page
                        career_links = find_career_links(driver)
                        if career_links:
                            print(f"    Found {len(career_links)} career link(s) on portfolio page")
                            for career_link in career_links:
                                if career_link and career_link not in result["career_pages"]:
                                    career_info = process_career_page(driver, career_link, timeout=10)
                                    result["career_pages"][career_link] = {
                                        "powered_by": career_info["powered_by"],
                                        "api_id": career_info["api_id"]
                                    }
                    except TimeoutException:
                        print(f"    Timeout loading portfolio page, skipping...")
                    except WebDriverException as e:
                        if "timeout" in str(e).lower():
                            print(f"    Portfolio page timeout, skipping...")
                        else:
                            print(f"    Error loading portfolio page: {str(e)[:100]}")
                    except Exception as e:
                        print(f"    Error processing portfolio link: {str(e)[:100]}")
        else:
            # Just check if the URL itself is a career page
            print("  Checking if URL is a career page...")
            career_info = process_career_page(driver, url, timeout=timeout)
            if career_info["powered_by"]:
                result["career_pages"][url] = {
                    "powered_by": career_info["powered_by"],
                    "api_id": career_info["api_id"]
                }
        return result
    except Exception as e:
        print(f"  Error processing URL {url}: {e}")
    
        return False

def save_results(results, output_file):
    """Save results to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {output_file}")
    except Exception as e:
        print(f"Error saving results: {e}")

def load_existing_results(output_file):
    """Load existing results from JSON file if it exists."""
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def main(crawl, portfolio, output_file, skip_existing_domains):
    # Load URLs from CSV file 'urls.csv' with header 'urls'
    try:
        urls_df = pd.read_csv("urls.csv")
        urls = urls_df["urls"].tolist()
    except Exception as e:
        print(f"Error reading urls.csv: {e}")
        return

    # Load existing results
    results = load_existing_results(output_file)
    processed_urls = {r["original_url"] for r in results if "original_url" in r}
    
    # Build domain index for merging
    domain_index = {}
    for i, r in enumerate(results):
        if "domain" in r and r["domain"]:
            domain_lower = r["domain"].lower()
            if domain_lower not in domain_index:
                domain_index[domain_lower] = i
    
    # Build set of existing domains if skip_existing_domains is True
    existing_domains = set(domain_index.keys())
    if skip_existing_domains and existing_domains:
        print(f"Found {len(existing_domains)} existing domains in results")
        print(f"Skip existing domains: {skip_existing_domains}")
    
    # Set up Chrome options
    options = Options()
    # Uncomment for headless mode:
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    # Set default page load timeout
    driver.set_page_load_timeout(20)  # Default 20 seconds for all page loads
    
    try:
        skipped_count = 0
        merged_count = 0
        
        for url in urls:
            # Normalize URL for checking
            check_url = url if url.startswith(("http://", "https://")) else f"http://{url}"
            
            # Skip if already processed (exact URL match)
            if url in processed_urls or check_url in processed_urls:
                print(f"Skipping {url} (URL already processed)")
                skipped_count += 1
                continue
            
            # Get domain for this URL
            domain = extract_domain(check_url)
            domain_lower = domain.lower() if domain else None
            
            # Check if domain already exists
            if domain_lower and domain_lower in existing_domains:
                if skip_existing_domains:
                    print(f"Skipping {url} (domain {domain} already exists)")
                    skipped_count += 1
                    continue
                else:
                    # Process and merge with existing domain
                    print(f"Processing {url} (will merge with existing domain {domain})")
                    
                    # Process the URL
                    url_result = process_url(driver, url, crawl=crawl, portfolio=portfolio)
                    if not url_result:
                        continue
                    
                    # Merge with existing domain entry
                    existing_idx = domain_index[domain_lower]
                    existing_entry = results[existing_idx]
                    
                    # Merge career pages
                    new_pages = url_result.get("career_pages", {})
                    if new_pages:
                        if "career_pages" not in existing_entry:
                            existing_entry["career_pages"] = {}
                        
                        # Count new career pages
                        before_count = len(existing_entry["career_pages"])
                        existing_entry["career_pages"].update(new_pages)
                        after_count = len(existing_entry["career_pages"])
                        new_count = after_count - before_count
                        
                        print(f"  Merged: Added {new_count} new career page(s) to existing {before_count}")
                        merged_count += 1
                    else:
                        print(f"  No new career pages found to merge")
            else:
                # New domain - process normally
                print(f"Processing {url} (new domain)")
                
                # Process the URL
                url_result = process_url(driver, url, crawl=crawl, portfolio=portfolio)
                if not url_result:
                    continue
                # Add to results
                results.append(url_result)
                
                # Update domain index
                if domain_lower:
                    domain_index[domain_lower] = len(results) - 1
                    existing_domains.add(domain_lower)
                
                # Summary for this URL
                career_count = len(url_result["career_pages"])
                if career_count > 0:
                    print(f"  Summary: Found {career_count} career page(s)")
                    for career_url, info in url_result["career_pages"].items():
                        if info["powered_by"]:
                            print(f"    - {career_url[:50]}... -> {info['powered_by']}")
                else:
                    print(f"  Summary: No career pages found")
            
            # Save after each URL (in case of crashes)
            save_results(results, output_file)
        
        if skipped_count > 0:
            print(f"\nSkipped {skipped_count} URLs (already processed)")
        if merged_count > 0:
            print(f"Merged {merged_count} URLs with existing domains")
    
    finally:
        driver.quit()
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total URLs processed: {len(results)}")
    
    urls_with_careers = sum(1 for r in results if r.get("career_pages"))
    print(f"URLs with career pages found: {urls_with_careers}")
    
    # Count by powered_by system
    system_counts = {}
    for result in results:
        for career_url, info in result.get("career_pages", {}).items():
            system = info.get("powered_by", "unknown")
            if system:
                system_counts[system] = system_counts.get(system, 0) + 1
    
    if system_counts:
        print("\nCareer pages by system:")
        for system, count in sorted(system_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {system}: {count}")

if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--crawl", action="store_true", help="Crawl pages for career links")
    parser.add_argument("-p", "--portfolio", action="store_true", help="Follow portfolio/investment links")
    parser.add_argument("-o", "--output", default="career_links.json", help="Output JSON file")
    parser.add_argument("--no-skip-domains", action="store_true", 
                        help="Process URLs even if their domain already exists in results (default: skip existing domains)")
    args = parser.parse_args()
    
    # If portfolio is True, crawl must also be True
    crawl = args.crawl
    portfolio = args.portfolio
    if portfolio and not crawl:
        crawl = True
    
    # skip_existing_domains is True by default, False if --no-skip-domains is passed
    skip_existing_domains = not args.no_skip_domains
    
    main(crawl, portfolio, args.output, skip_existing_domains)