import requests
import json
import time
import os
from bs4 import BeautifulSoup

def get_investor_list_slugs():
    """Fetch and parse investor list slugs from NFX login page"""
    login_url = "https://signal.nfx.com/login"
    
    try:
        # Use curl-like headers to match your successful request
        headers = {
            'User-Agent': 'curl/7.68.0',
            'Accept': '*/*'
        }
        
        response = requests.get(login_url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        slugs = []
        
        # Find ALL <a> tags and check their hrefs
        all_links = soup.find_all('a')
        print(f"Scanning {len(all_links)} links for investor lists...")
        
        for link in all_links:
            href = link.get('href', '')
            # Check if this is an investor list link
            if 'investor-lists' in href:
                # Extract slug from URL like: /investor-lists/top-enterprise-seed-investors
                # We want just: enterprise-seed
                if '/top-' in href and '-investors' in href:
                    # Extract everything between 'top-' and '-investors'
                    parts = href.split('/top-')
                    if len(parts) > 1:
                        slug_part = parts[1].replace('-investors', '')
                        if slug_part and slug_part not in slugs:
                            slugs.append(slug_part)
        
        print(f"Found {len(slugs)} unique investor list slugs")
        for slug in slugs[:5]:  # Show first 5 as examples
            print(f"  - {slug}")
        if len(slugs) > 5:
            print(f"  ... and {len(slugs) - 5} more")
        
        return slugs
    
    except Exception as e:
        print(f"Error fetching slugs: {e}")
        return []

# Get all valid slugs
slugs = get_investor_list_slugs()

if not slugs:
    print("No slugs found, using default slug")
    slugs = ["consumer-internet-pre-seed"]  # Fallback to original slug

url = "https://signal-api.nfx.com/graphql"

headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'PostmanRuntime/7.29.4',
    'Accept': '*/*',
    'Host': 'signal-api.nfx.com',
    'Connection': 'keep-alive',
    # Removed Accept-Encoding to let requests handle compression automatically
}

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Load existing data to avoid duplicates
try:
    with open(f"data/nfx-investors-api-2.json") as f:
        file_data = [(json.loads(line))['slug'] for line in f]
except FileNotFoundError:
    file_data = []
    print("No existing data file found, starting fresh")

# Loop through each slug
for list_slug in slugs:
    print(f"\n{'='*50}")
    print(f"Processing investor list: {list_slug}")
    print(f"{'='*50}")
    
    payload = {
      "operationName": "vclInvestors",
      "variables": {
        "slug": list_slug,
        "order": [
          {}
        ],
        "after": None
      },
     "query": "query vclInvestors($slug: String!, $after: String) {\n  list(slug: $slug) {\n    id\n    slug\n    investor_count\n    vertical {\n      id\n      display_name\n      kind\n      __typename\n    }\n    location {\n      id\n      display_name\n      __typename\n    }\n    stage\n    firms {\n      id\n      name\n      slug\n      __typename\n    }\n    scored_investors(first: 8, after: $after) {\n      pageInfo {\n        hasNextPage\n        hasPreviousPage\n        endCursor\n        __typename\n      }\n      record_count\n      edges {\n        node {\n          ...investorListInvestorProfileFields\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment investorListInvestorProfileFields on InvestorProfile {\n  id\n  person {\n    id\n    first_name\n    last_name\n    name\n    slug\n    is_me\n    is_on_target_list\n    __typename\n  }\n  image_urls\n  position\n  min_investment\n  max_investment\n  target_investment\n  is_preferred_coinvestor\n  firm {\n    id\n    name\n    slug\n    __typename\n  }\n  investment_locations {\n    id\n    display_name\n    location_investor_list {\n      id\n      slug\n      __typename\n    }\n    __typename\n  }\n  investor_lists {\n    id\n    stage_name\n    slug\n    vertical {\n      id\n      display_name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
    }
    
  
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        print(f"error {response.status_code}")
        print(response.text)
        break  # Skip to next slug on error
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response for {list_slug}: {e}")
        print(f"Response content preview: {response.text[:200]}...")
        break
        
    # Check if we got valid data
    if 'data' not in data or 'list' not in data['data']:
        print(f"Invalid response for slug {list_slug}")
        break
    
    firms = data['data']['list']['firms']
    print(f"Found {len(firms)} firms in this list")
    
    for firm in firms:
        try:
            firm_data = {}
            firm_data['id'] = firm['id']
            firm_data['name'] = firm['name']
            firm_data['slug'] = firm['slug']
            
            if firm_data['slug'] in file_data:
                print(f"  Skipping {firm_data['name']} (already exists)")
                continue
            
            print(f"  Processing investor: {firm_data['name']} ({firm_data['slug']})")
            investor_payload = json.dumps({
                "operationName": "FirmForFirmPageQuery",
                "variables": {
                    "slug": firm_data['slug']
                },
                "query": "query FirmForFirmPageQuery($slug: String!) {\n  firm(slug: $slug) {\n    id\n    slug\n    name\n    angellist_url\n    twitter_url\n    linkedin_url\n    url\n    crunchbase_url\n    description\n    founding_year\n    investor_lists {\n      id\n      stage_name\n      vertical {\n        id\n        display_name\n        __typename\n      }\n      __typename\n    }\n    locations {\n      id\n      display_name\n      __typename\n    }\n    coinvested_firms {\n      id\n      name\n      slug\n      __typename\n    }\n    investor_profiles {\n      ...investorListInvestorProfileFields\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment investorListInvestorProfileFields on InvestorProfile {\n  id\n  person {\n    id\n    first_name\n    last_name\n    name\n    slug\n    is_me\n    is_on_target_list\n    __typename\n  }\n  image_urls\n  position\n  min_investment\n  max_investment\n  target_investment\n  is_preferred_coinvestor\n  firm {\n    id\n    name\n    slug\n    __typename\n  }\n  investment_locations {\n    id\n    display_name\n    location_investor_list {\n      id\n      slug\n      __typename\n    }\n    __typename\n  }\n  investor_lists {\n    id\n    stage_name\n    slug\n    vertical {\n      id\n      display_name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
            })

            investor_response = requests.request("POST", url, headers=headers, data=investor_payload)
            details = investor_response.json()
        
            firm_data['linkedin'] = details['data']['firm']['linkedin_url']
            firm_data['twitter'] = details['data']['firm']['twitter_url']
            firm_data['crunchbase'] = details['data']['firm']['crunchbase_url']
            firm_data['url'] = details['data']['firm']['url']
            print(f"  Added: {firm_data['name']}")
            
            # Add to file_data to avoid duplicates within this run
            file_data.append(firm_data['slug'])
            
            with open(f"data/nfx-investors-api-2.json", "a+") as file:
                file.write(json.dumps(firm_data) + "\n")
        except Exception as e:
            print(f"  Error processing investor: {e}")
            if 'investor_response' in locals():
                print(f"  Response: {investor_response.text[:200]}...")
            continue
        time.sleep(1)

print(f"\n{'='*50}")
print(f"Scraping complete! Processed {len(slugs)} investor lists")
print(f"{'='*50}")
