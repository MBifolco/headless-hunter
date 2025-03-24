import pandas as pd
import json
from urllib.parse import urlparse

# Load the CSV file that contains the career links
csv_file = "career_links.csv"
df = pd.read_csv(csv_file)

# Filter for rows where powered_by equals "getro"
df_getro = df[df["powered_by"].str.lower() == "getro"]

def extract_getro_id_and_construct_url(career_url):
    """
    Given a career_url, extract the subdomain and construct the final URL.
    Expected career_url is something like 'https://careers.antler.co/anything'.
    The final URL will be in the format:
         https://{subdomain}/jobs
    And the id will be extracted from the subdomain (removing the "careers." prefix).
    """
    parsed = urlparse(career_url)
    netloc = parsed.netloc  # e.g. "careers.antler.co"
    final_url = f"https://{netloc}/jobs"
    
    # Extract id: if netloc starts with "careers.", remove it and take the first token.
    if netloc.startswith("careers."):
        remaining = netloc[len("careers."):]
        site_id = remaining.split('.')[0]
    else:
        # Fallback: take the first part of the netloc
        site_id = netloc.split('.')[0]
    return site_id, final_url

getro_sites = []

for _, row in df_getro.iterrows():
    career_url = row["career_url"]
    if pd.isnull(career_url) or career_url.strip() == "":
        continue
    site_id, final_url = extract_getro_id_and_construct_url(career_url)
    # Generate a friendly name from the id by splitting on hyphens and capitalizing words.
    name = " ".join(word.capitalize() for word in site_id.split("-"))
    site_dict = {
        "id": site_id,
        "name": name,
        "type": "getro",
        "url": final_url
    }
    getro_sites.append(site_dict)

# Remove duplicates (if multiple rows yield the same id)
unique_sites = {site['id']: site for site in getro_sites}.values()
unique_sites = list(unique_sites)

# Write the list of dictionaries to getro_sites.json
with open("getro_sites.json", "w", encoding="utf-8") as f:
    json.dump(unique_sites, f, indent=4)

print("getro_sites.json has been created.")
