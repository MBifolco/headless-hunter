import os
import csv
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

RESULTS_CSV = "career_links.csv"

def write_to_csv(found_on_url, career_url, powered_by, consider_id):
    """Append a new row to the results CSV with source URL, career URL, powered_by info and consider id if applicable."""
    file_exists = os.path.isfile(RESULTS_CSV)
    with open(RESULTS_CSV, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["found_on_url", "career_url", "powered_by", "id"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "found_on_url": found_on_url,
            "career_url": career_url,
            "powered_by": powered_by,
            "id": consider_id
        })

def contains_keyword(text, keywords):
    """Return True if the text contains any of the keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

def find_career_links(driver):
    """
    Search for any <a> or <button> elements whose visible text contains "careers" or "jobs".
    Returns a list of target URLs (or empty strings if no href is available).
    """
    elements = driver.find_elements(By.XPATH, "//a | //button")
    career_links = []
    for element in elements:
        try:
            if element.text and contains_keyword(element.text, ["careers", "jobs"]):
                href = element.get_attribute("href") if element.tag_name.lower() == "a" else ""
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
                if href:
                    links.append(href)
        except Exception:
            continue
    return links

def get_powered_by_info(driver):
    """
    Check the current page for "Powered by Getro" or "Powered by Consider".
    If "Powered by Consider" is found, attempt to extract the additional id from a div with class "boards-body".
    Returns a tuple (powered_by, consider_id) where powered_by is "getro", "consider", or an empty string.
    """
    powered_by = ""
    consider_id = ""
    page_source = driver.page_source
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
                consider_id = other_classes[0]
        except Exception:
            pass
    elif "Powered by Getro" in page_source:
        powered_by = "getro"
    return powered_by, consider_id

def process_career_link(driver, source_url, career_link):
    """
    Given a career_link URL, navigate to that URL to search for powered-by info.
    Then record the result in the CSV.
    """
    powered_by = ""
    consider_id = ""
    if career_link:
        try:
            driver.get(career_link)
            time.sleep(2)  # Allow the career page to load
            powered_by, consider_id = get_powered_by_info(driver)
        except Exception as e:
            print(f"Error processing career link {career_link}: {e}")
    print(f"Recording: found_on_url={source_url}, career_url={career_link}, powered_by={powered_by}, id={consider_id}")
    write_to_csv(source_url, career_link, powered_by, consider_id)

def main():
    # Load URLs from CSV file 'urls.csv' with header 'urls'
    urls_df = pd.read_csv("urls.csv")
    urls = urls_df["urls"].tolist()

    # Set up Chrome options (using headless mode)
    options = Options()
    #options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    for url in urls:
        if "http" not in url:
            url = "http://" + url  # Ensure URL starts with http if not present
        print(f"Processing main URL: {url}")
        try:
            driver.get(url)
            time.sleep(2)  # Allow time for the page to load

            # Search for careers/jobs links on the main page.
            career_links = find_career_links(driver)
            if career_links:
                for career_link in career_links:
                    process_career_link(driver, url, career_link)
                continue  # Move to next main URL if a career link is found

            # If no careers/jobs links on the main page, check for portfolio/investments links.
            portfolio_links = get_portfolio_investment_links(driver)
            found_in_portfolio = False
            for p_link in portfolio_links:
                print(f"Following portfolio/investments link: {p_link}")
                try:
                    driver.get(p_link)
                    time.sleep(2)  # Allow the secondary page to load
                    career_links = find_career_links(driver)
                    if career_links:
                        for career_link in career_links:
                            process_career_link(driver, p_link, career_link)
                        found_in_portfolio = True
                        break  # Once a match is found, move to the next main URL
                except Exception as e:
                    print(f"Error processing portfolio link {p_link}: {e}")
                    continue

            if not career_links and not found_in_portfolio:
                print(f"No careers/jobs links found for main URL: {url}")

        except Exception as e:
            print(f"Error processing main URL {url}: {e}")
            continue

    driver.quit()

if __name__ == "__main__":
    main()
