#!/usr/bin/env python3
"""
Script to find unique domains from career_links.csv that don't have a known job board system.
Outputs a list of domains where we haven't identified the powering system.
"""

import csv
import sys
from urllib.parse import urlparse
from collections import defaultdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

def extract_domain(url):
    """Extract the domain from a URL, normalizing by removing www prefix."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain and parsed.path:
            # Handle cases where URL might not have scheme
            parsed = urlparse(f"http://{url}")
            domain = parsed.netloc
        
        # Normalize domain by removing www. prefix
        if domain:
            domain = domain.lower()
            if domain.startswith('www.'):
                domain = domain[4:]  # Remove 'www.' prefix
        
        return domain if domain else None
    except Exception:
        return None

def main(input_csv, output_csv):
    """
    Read career_links.csv and output domains without identified systems.
    Only includes domains where an actual career URL was found (different from source).
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file
    """
    # Track domains and their powered_by status
    domain_systems = defaultdict(set)
    # Track domains that had actual career URLs found (not same as source)
    domains_with_career_urls = set()
    # Track example career_urls for each domain (preserving original URL with www)
    domain_career_urls = {}
    
    # Read the CSV file
    try:
        with open(input_csv, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                found_on_url = row.get('found_on_url', '')
                career_url = row.get('career_url', '')
                powered_by = row.get('powered_by', '').strip()
                
                # Extract domains from both URLs (normalized without www)
                found_domain = extract_domain(found_on_url)
                career_domain = extract_domain(career_url)
                
                # Check if career_url is different from found_on_url (actual career page found)
                if found_on_url and career_url and found_on_url.strip() != career_url.strip():
                    if found_domain:
                        domains_with_career_urls.add(found_domain)
                        # Store the first career_url we see for this domain (preserving www)
                        if found_domain not in domain_career_urls:
                            domain_career_urls[found_domain] = career_url
                    if career_domain:
                        domains_with_career_urls.add(career_domain)
                        # Store the first career_url we see for this domain (preserving www)
                        if career_domain not in domain_career_urls:
                            domain_career_urls[career_domain] = career_url
                
                # Track the powered_by info for each domain
                if found_domain:
                    if powered_by:
                        domain_systems[found_domain].add(powered_by)
                    else:
                        # Add empty string to indicate we've seen this domain but no system
                        domain_systems[found_domain].add('')
                
                if career_domain and career_domain != found_domain:
                    if powered_by:
                        domain_systems[career_domain].add(powered_by)
                    else:
                        domain_systems[career_domain].add('')
    
    except FileNotFoundError:
        print(f"Error: Could not find file '{input_csv}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Find domains without any known systems that had actual career URLs
    unknown_domains = []
    for domain, systems in domain_systems.items():
        # Only include if domain had actual career URLs found AND no known system
        if domain in domains_with_career_urls:
            if systems == {''} or ('' in systems and len(systems) == 1):
                unknown_domains.append(domain)
    
    # Sort domains alphabetically
    unknown_domains.sort()
    
    # Output results
    print(f"\nFound {len(unknown_domains)} unique domains without identified job board systems")
    print(f"(filtered to only domains where career URLs were found)")
    print("-" * 60)
    
    for domain in unknown_domains[:10]:  # Show first 10 as preview
        url = domain_career_urls.get(domain, '')
        print(f"{domain} | {url}")
    if len(unknown_domains) > 10:
        print(f"... and {len(unknown_domains) - 10} more")
    
    # Write to output CSV with career_url
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['domain', 'career_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for domain in unknown_domains:
                writer.writerow({
                    'domain': domain,
                    'career_url': domain_career_urls.get(domain, '')
                })
        
        print(f"\nResults saved to '{output_csv}'")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)
    
    # Summary statistics
    total_domains = len(domain_systems)
    domains_with_urls_count = len(domains_with_career_urls)
    known_with_urls = domains_with_urls_count - len(unknown_domains)
    
    print(f"\nSummary:")
    print(f"  Total unique domains: {total_domains}")
    print(f"  Domains with actual career URLs found: {domains_with_urls_count}")
    print(f"  - With known systems: {known_with_urls}")
    print(f"  - With unknown systems: {len(unknown_domains)}")
    
    if domains_with_urls_count > 0:
        coverage = (known_with_urls / domains_with_urls_count) * 100
        print(f"  Coverage for domains with career URLs: {coverage:.1f}%")

if __name__ == "__main__":
    parser = ArgumentParser(
        description='Find domains from career_links.csv without identified job board systems',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-i', '--input_csv',
        default='career_links.csv',
        help='Input CSV file'
    )
    parser.add_argument(
        '-o', '--output_csv',
        default='unknown_systems.csv',
        help='Output CSV file'
    )
    
    args = parser.parse_args()
    main(args.input_csv, args.output_csv)
