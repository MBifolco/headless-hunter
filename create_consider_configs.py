import pandas as pd
import json
from urllib.parse import urlparse

# Load the CSV file that contains the career links
csv_file = "career_links.csv"
df = pd.read_csv(csv_file)

# Filter rows where the page was "Powered by Consider"
df_consider = df[df["powered_by"].str.lower() == "consider"]

# Optionally remove duplicate entries based on the 'id' column.
df_consider = df_consider.drop_duplicates(subset=["id"])

consider_sites = []

for _, row in df_consider.iterrows():
    career_url = row["career_url"]
    # Use urlparse to extract the netloc (subdomain)
    parsed = urlparse(career_url)
    subdomain = parsed.netloc  # This should be like "jobs.xyz.com"
    
    # Construct the desired API URL
    constructed_url = f"https://{subdomain}/api-boards/search-jobs"
    
    # Get the id from the CSV row (expected to be something like "sequoia-capital")
    site_id = row["id"].strip()
    
    # Create a friendly name by replacing hyphens with spaces and capitalizing words
    name = " ".join(word.capitalize() for word in site_id.split("-"))
    
    site_dict = {
        "id": site_id,
        "name": name,
        "type": "consider",
        "url": constructed_url
    }
    consider_sites.append(site_dict)

# Save the list of dictionaries to consider_sites.json
with open("consider_sites.json", "w", encoding="utf-8") as f:
    json.dump(consider_sites, f, indent=4)

print("consider_sites.json has been created.")
