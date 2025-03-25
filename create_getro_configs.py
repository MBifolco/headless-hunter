import argparse
import os
import json
import pandas as pd
from urllib.parse import urlparse
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pprint import pprint as pp
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
    
    site_id = netloc.split('.')[1]
    return site_id, final_url

def main(input_csv):
    # Load the CSV file that contains the career links.
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"Error reading CSV file {input_csv}: {e}")
        return

    # Filter for rows where powered_by equals "getro"
    df_getro = df[df["powered_by"].str.lower() == "getro"]
    print(f"Found {len(df_getro)} Getro sites.")
    getro_sites = []
    for _, row in df_getro.iterrows():
        career_url = row["career_url"]
        if pd.isnull(career_url) or career_url.strip() == "":
            print("Skipping empty career_url.")
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
    print(f"Found {len(unique_sites)} unique Getro sites.")
    # Define the output JSON file.
    output_json = "getro_sites.json"
    
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
    for site in unique_sites:
        if site["id"] not in existing_ids:
            existing_sites.append(site)
            print(f"Added new site: {site['id']}")
        else:
            print(f"Site {site['id']} already exists; skipping.")

    # Write the updated list back to getro_sites.json.
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
