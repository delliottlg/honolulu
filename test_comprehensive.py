#!/usr/bin/env python3
"""Test the comprehensive Honolulu glass industry scraper"""

from honolulu_scraper import scrape_honolulu_glass_industry

# Your SerpAPI key
API_KEY = "69ba8b9b642039edc041e7259c22bcf76072009bc53150bcbb810b9cbd726a6d"

print("Starting comprehensive Honolulu glass industry scraping...")
print("=" * 60)

result = scrape_honolulu_glass_industry(API_KEY)

print("\n" + "=" * 60)
print("Scraping Complete!")
print(f"   Found: {result['found']} businesses")
print(f"   Saved: {result['saved']} new businesses")
print("=" * 60)