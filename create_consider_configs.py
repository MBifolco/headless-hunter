import argparse
import os
import json
import pandas as pd
from urllib.parse import urlparse
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

def main(input_csv):
    # Load the CSV file that contains the career links.
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"Error reading CSV file {input_csv}: {e}")
        return

    # Filter rows where the page was "Powered by Consider"
    df_consider = df[df["powered_by"].str.lower() == "consider"]
    print(f"Found {len(df_consider)} Consider sites.")
    # Optionally remove duplicate entries based on the 'id' column.
    df_consider = df_consider.drop_duplicates(subset=["id"])
    print(f"Found {len(df_consider)} unique Consider sites.")
    new_sites = []
    for _, row in df_consider.iterrows():
        career_url = row["career_url"]
        # Use urlparse to extract the netloc (e.g. "jobs.xyz.com")
        parsed = urlparse(career_url)
        subdomain = parsed.netloc
        # Construct the desired API URL
        constructed_url = f"https://{subdomain}/api-boards/search-jobs"
        # Get the id from the CSV row (e.g. "sequoia-capital")
        site_id = row["id"].strip()
        # Create a friendly name by replacing hyphens with spaces and capitalizing each word.
        name = " ".join(word.capitalize() for word in site_id.split("-"))
        
        site_dict = {
            "id": site_id,
            "name": name,
            "type": "consider",
            "url": constructed_url
        }
        new_sites.append(site_dict)

    # Define the output JSON file.
    output_json = "consider_sites.json"
    
    # Load existing sites from the JSON file if it exists.
    if os.path.exists(output_json):
        try:
            with open(output_json, "r", encoding="utf-8") as f:
                existing_sites = json.load(f)
        except Exception as e:
            print(f"Error loading {output_json}: {e}")
            existing_sites = []
    else:
        existing_sites = []

    # Create a set of existing site ids for quick lookup.
    existing_ids = {site["id"] for site in existing_sites}

    # Append only new sites that are not already in existing_ids.
    for site in new_sites:
        if site["id"] not in existing_ids:
            existing_sites.append(site)
            print(f"Added new site: {site['id']}")
        else:
            print(f"Site {site['id']} already exists; skipping.")

    # Write the updated list back to consider_sites.json.
    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(existing_sites, f, indent=4)
        print(f"{output_json} has been updated.")
    except Exception as e:
        print(f"Error writing to {output_json}: {e}")

if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_csv", default="career_links.csv", type=str, help="Input CSV file")
    args = vars(parser.parse_args())
    input_csv = args["input_csv"]
    main(input_csv)
