#!/usr/bin/env python3
"""
Convert NFX scraping results (JSON lines format) to urls.csv for processing with find_listings.py

Usage:
    python nfx_to_urls.py                           # Use default input/output
    python nfx_to_urls.py -i data/nfx.json -o urls.csv
    python nfx_to_urls.py --unique                  # Only output unique domains
"""

import json
import csv
import os
import argparse
from urllib.parse import urlparse

def extract_urls_from_nfx_data(input_file, unique_domains=False):
    """
    Extract URLs from NFX investor data file (JSON lines format).
    
    Args:
        input_file: Path to NFX JSON lines file
        unique_domains: If True, only return one URL per domain
    
    Returns:
        List of URLs
    """
    urls = []
    seen_domains = set()
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return urls
    
    print(f"Reading NFX data from: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            line_count = 0
            for line in f:
                line_count += 1
                if not line.strip():
                    continue
                
                try:
                    # Parse JSON line
                    data = json.loads(line)
                    
                    # Extract URL field (could be 'url' or 'website' depending on format)
                    url = data.get('url') or data.get('website') or data.get('company_url')
                    
                    if url and url.strip():
                        # Clean up the URL
                        url = url.strip()
                        
                        # Skip if it's not a valid URL
                        if url in ['None', 'null', 'N/A', '']:
                            continue
                        
                        # Skip social media and other non-company URLs
                        skip_domains = [
                            'linkedin.com', 'twitter.com', 'facebook.com', 
                            'crunchbase.com', 'angellist.com', 'github.com',
                            'youtube.com', 'instagram.com', 'medium.com'
                        ]
                        
                        if any(domain in url.lower() for domain in skip_domains):
                            continue
                        
                        # If unique_domains is True, check if we've seen this domain
                        if unique_domains:
                            try:
                                parsed = urlparse(url if url.startswith(('http://', 'https://')) else f'http://{url}')
                                domain = parsed.netloc or parsed.path
                                domain = domain.lower()
                                
                                if domain in seen_domains:
                                    continue
                                
                                seen_domains.add(domain)
                            except:
                                pass
                        
                        urls.append(url)
                        
                        # Also check for LinkedIn URL that might contain company website
                        linkedin = data.get('linkedin')
                        if linkedin and '/company/' in linkedin:
                            # Some LinkedIn company pages might have websites, but we'll skip these
                            pass
                
                except json.JSONDecodeError as e:
                    print(f"  Warning: Failed to parse JSON on line {line_count}: {e}")
                    continue
                except Exception as e:
                    print(f"  Warning: Error processing line {line_count}: {e}")
                    continue
        
        print(f"Processed {line_count} lines")
        print(f"Found {len(urls)} valid URLs")
        if unique_domains:
            print(f"Unique domains: {len(seen_domains)}")
            
    except Exception as e:
        print(f"Error reading file: {e}")
    
    return urls

def save_urls_to_csv(urls, output_file):
    """
    Save URLs to CSV file with 'urls' as header.
    
    Args:
        urls: List of URLs
        output_file: Path to output CSV file
    """
    if not urls:
        print("No URLs to save")
        return False
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['urls'])
            # Write URLs
            for url in urls:
                writer.writerow([url])
        
        print(f"\nSuccessfully saved {len(urls)} URLs to: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Convert NFX investor data to urls.csv for find_listings.py',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '-i', '--input',
        default='data/nfx-investors-api-2.json',
        help='Input NFX JSON lines file'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='urls.csv',
        help='Output CSV file'
    )
    
    parser.add_argument(
        '--unique',
        action='store_true',
        help='Only output one URL per unique domain'
    )
    
    parser.add_argument(
        '--preview',
        type=int,
        metavar='N',
        help='Preview first N URLs without saving'
    )
    
    args = parser.parse_args()
    
    # Extract URLs from NFX data
    urls = extract_urls_from_nfx_data(args.input, unique_domains=args.unique)
    
    if not urls:
        print("No URLs found to process")
        return
    
    # Preview mode
    if args.preview:
        print(f"\nPreview of first {args.preview} URLs:")
        print("-" * 60)
        for i, url in enumerate(urls[:args.preview], 1):
            print(f"{i:3}. {url}")
        if len(urls) > args.preview:
            print(f"... and {len(urls) - args.preview} more")
        print("-" * 60)
        response = input("\nProceed to save? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    
    # Save to CSV
    save_urls_to_csv(urls, args.output)
    
    # Show summary
    print("\nYou can now run:")
    print(f"  python find_listings.py -c")
    print(f"  python find_listings.py -c -p  # Also check portfolio pages")
    print(f"  python find_listings.py -c --no-skip-domains  # Process all URLs even if domain exists")

if __name__ == "__main__":
    main()