#!/usr/bin/env python3
"""
Update all job board configuration files from career_links.json

This script reads the career_links.json file created by find_listings.py
and updates the configuration files for each supported job board system:
- consider_sites.json
- getro_sites.json  
- greenhouse_sites.json
- ventureloop_sites.json

Usage:
    python update_configs_from_json.py
    python update_configs_from_json.py -i career_links.json
    python update_configs_from_json.py --dry-run
"""

import json
import os
import argparse
from urllib.parse import urlparse
from collections import defaultdict

def extract_site_id_from_url(url, powered_by):
    """Extract site ID from domain name (not subdomain)."""
    parsed = urlparse(url)
    netloc = parsed.netloc
    
    # Special case for greenhouse URLs like boards.greenhouse.io/company
    if powered_by == "greenhouse" and "greenhouse.io" in netloc:
        path_parts = parsed.path.strip('/').split('/')
        if path_parts and path_parts[0]:
            return path_parts[0]
    
    # For all other cases, extract the main domain name
    # Remove any subdomain and TLD to get just the domain
    # e.g., careers.example.com -> example
    # e.g., jobs.company.co.uk -> company
    parts = netloc.split('.')
    
    if len(parts) >= 2:
        # Handle different TLD patterns
        # For .com, .org, .io, etc. - take second to last part
        # For .co.uk, .com.au, etc. - still take the part before the TLD
        if len(parts) >= 3 and parts[-2] in ['co', 'com', 'org', 'net', 'edu', 'gov']:
            # Multi-part TLD like .co.uk
            return parts[-3]
        else:
            # Standard TLD like .com
            return parts[-2]
    elif len(parts) == 1:
        # Just a domain without TLD (shouldn't happen but handle it)
        return parts[0]
    
    return None

def create_site_config(site_id, name, powered_by, url, api_id=None):
    """Create a site configuration dict."""
    config = {
        "id": site_id,
        "name": name,
        "type": powered_by
    }
    
    if powered_by == "consider":
        # Consider uses API endpoint
        parsed = urlparse(url)
        config["url"] = f"https://{parsed.netloc}/api-boards/search-jobs"
    
    elif powered_by == "getro":
        # Getro uses /jobs endpoint
        parsed = urlparse(url)
        config["url"] = f"https://{parsed.netloc}/jobs"
    
    elif powered_by == "greenhouse":
        # Greenhouse uses API with ID
        if api_id:
            config["url"] = f"https://boards-api.greenhouse.io/v1/boards/{api_id}/jobs"
        else:
            config["url"] = f"https://boards-api.greenhouse.io/v1/boards/{site_id}/jobs"
    
    elif powered_by == "ventureloop":
        # VentureLoop uses the direct career URL
        config["url"] = url
    
    else:
        # Default: use the provided URL
        config["url"] = url
    
    return config

def load_career_links(input_file):
    """Load and parse career_links.json file."""
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return []

def extract_sites_by_system(career_data):
    """Extract and organize sites by job board system."""
    sites_by_system = defaultdict(list)
    processed = defaultdict(set)  # Track processed site IDs per system
    
    for entry in career_data:
        career_pages = entry.get("career_pages", {})
        
        for career_url, info in career_pages.items():
            powered_by = info.get("powered_by", "").lower()
            api_id = info.get("api_id", "")
            
            if not powered_by:
                continue
            
            # Only process supported systems
            if powered_by not in ["consider", "getro", "greenhouse", "ventureloop"]:
                continue
            
            # Extract site ID
            site_id = api_id if api_id else extract_site_id_from_url(career_url, powered_by)
            
            if not site_id:
                print(f"  Warning: Could not extract site ID from {career_url} ({powered_by})")
                continue
            
            # Skip if already processed
            if site_id in processed[powered_by]:
                continue
            
            processed[powered_by].add(site_id)
            
            # Create friendly name
            name = " ".join(word.capitalize() for word in site_id.replace("-", " ").replace("_", " ").split())
            
            # Create site config
            site_config = create_site_config(site_id, name, powered_by, career_url, api_id)
            sites_by_system[powered_by].append(site_config)
    
    return sites_by_system

def load_existing_config(filename):
    """Load existing configuration file."""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  Warning: Error loading {filename}: {e}")
            return []
    return []

def update_config_file(filename, new_sites, dry_run=False):
    """Update a configuration file with new sites."""
    existing_sites = load_existing_config(filename)
    existing_ids = {site["id"] for site in existing_sites}
    
    added_count = 0
    for site in new_sites:
        if site["id"] not in existing_ids:
            if not dry_run:
                existing_sites.append(site)
            print(f"    + Adding: {site['id']} ({site['name']})")
            added_count += 1
        else:
            # Site already exists
            pass
    
    if added_count > 0:
        if not dry_run:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(existing_sites, f, indent=4)
                print(f"  Updated {filename}: Added {added_count} new sites")
            except Exception as e:
                print(f"  Error writing to {filename}: {e}")
        else:
            print(f"  [DRY RUN] Would add {added_count} new sites to {filename}")
    else:
        print(f"  No new sites to add to {filename}")
    
    return added_count

def main():
    parser = argparse.ArgumentParser(
        description='Update job board configuration files from career_links.json',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '-i', '--input',
        default='career_links.json',
        help='Input career links JSON file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    
    parser.add_argument(
        '--systems',
        nargs='+',
        choices=['consider', 'getro', 'greenhouse', 'ventureloop'],
        help='Only update specific systems (default: all)'
    )
    
    args = parser.parse_args()
    
    # Load career links data
    print(f"Loading career links from: {args.input}")
    career_data = load_career_links(args.input)
    
    if not career_data:
        print("No data found to process")
        return
    
    print(f"Found {len(career_data)} entries in career links file")
    
    # Extract sites by system
    sites_by_system = extract_sites_by_system(career_data)
    
    # Summary of found sites
    print("\nSites found by system:")
    for system, sites in sites_by_system.items():
        print(f"  {system}: {len(sites)} sites")
    
    if args.dry_run:
        print("\n[DRY RUN MODE - No files will be modified]")
    
    # Update configuration files
    config_files = {
        "consider": "consider_sites.json",
        "getro": "getro_sites.json",
        "greenhouse": "greenhouse_sites.json",
        "ventureloop": "ventureloop_sites.json"
    }
    
    systems_to_update = args.systems if args.systems else config_files.keys()
    total_added = 0
    
    print("\nUpdating configuration files:")
    for system in systems_to_update:
        if system not in sites_by_system:
            print(f"\n{system.capitalize()}:")
            print(f"  No new sites found")
            continue
        
        print(f"\n{system.capitalize()}:")
        filename = config_files[system]
        new_sites = sites_by_system[system]
        added = update_config_file(filename, new_sites, dry_run=args.dry_run)
        total_added += added
    
    # Final summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total new sites added: {total_added}")
    if args.dry_run:
        print("[DRY RUN - No files were actually modified]")
    else:
        print("Configuration files have been updated")
    
    # Show next steps
    if total_added > 0 and not args.dry_run:
        print("\nNext steps:")
        print("  1. Review the updated configuration files")
        print("  2. Run the job scraper: python search.py")

if __name__ == "__main__":
    main()