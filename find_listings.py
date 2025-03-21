import os
import csv
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# CSV file to save results (updated each time a match is found)
RESULTS_CSV = "career_links.csv"

def write_to_csv(found_on_url, career_url):
    """Append a new row to the results CSV with the source URL and scraped career URL."""
    file_exists = os.path.isfile(RESULTS_CSV)
    with open(RESULTS_CSV, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["found_on_url", "career_url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({"found_on_url": found_on_url, "career_url": career_url})

def contains_keyword(text, keywords):
    """Return True if the text contains any keyword (case-insensitive)."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

def find_career_links(driver):
    """
    Search for any <a> or <button> elements with visible text containing "careers" or "jobs".
    Returns a list of target URLs (or empty strings if no href is present).
    """
    elements = driver.find_elements(By.XPATH, "//a | //button")
    career_links = []
    for element in elements:
        try:
            if element.text and contains_keyword(element.text, ["careers", "jobs", "join us", "work with us"]):
                # Only <a> tags typically have an href attribute.
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
            if element.text and contains_keyword(element.text, ["portfolio", "investments", "companies"]):
                href = element.get_attribute("href")
                if href:
                    links.append(href)
        except Exception:
            continue
    return links

def main():
    # Load the list of URLs from a CSV with header "urls"
    urls_df = pd.read_csv("urls.csv")
    urls = urls_df["urls"].tolist()

    # Set up Chrome options (using headless mode)
    options = Options()
    #options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    for url in urls:
        print(f"Processing main URL: {url}")
        try:
            driver.get(url)
            time.sleep(2)  # Allow time for the page to load

            # Search for careers/jobs on the main page.
            career_links = find_career_links(driver)
            if career_links:
                for career_link in career_links:
                    print(f"Found careers/jobs link on main page: {career_link}")
                    write_to_csv(url, career_link)
                # Continue to next main URL if any match is found.
                continue

            # If not found, look for portfolio/investments links.
            portfolio_links = get_portfolio_investment_links(driver)
            found_in_portfolio = False
            for p_link in portfolio_links:
                print(f"Following portfolio/investments link: {p_link}")
                try:
                    driver.get(p_link)
                    time.sleep(2)  # Wait for the secondary page to load
                    career_links = find_career_links(driver)
                    if career_links:
                        for career_link in career_links:
                            print(f"Found careers/jobs link on portfolio/investments page: {career_link}")
                            write_to_csv(p_link, career_link)
                        found_in_portfolio = True
                        break  # Move to the next main URL once a match is found
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
