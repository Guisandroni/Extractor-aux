import os
import time
import json
import random
import requests
import pandas as pd
import google.generativeai as genai
from bs4 import BeautifulSoup
from typing import List, Dict, Any

# Configuration
MODEL_NAME = "gemini-2.0-flash"
OUTPUT_FILE = "results/items_extracted.json"
SITES_FILE = "aux/sites_de_leilao.txt"
BATCH_SIZE = 5

def setup_environment():
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set.")
        return False
    genai.configure(api_key=api_key)
    return True

def fetch_html(url: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }
    try:
        if not url.startswith("http"):
            url = f"https://{url}"
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Basic charset detection fix if needed
        if response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding
            
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def simplify_html(html: str) -> str:
    """
    Strips unnecessary tags to reduce token usage and noise for the LLM.
    """
    if not html:
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script, style, svg, paths, etc.
    for tag in soup(["script", "style", "svg", "path", "noscript", "meta", "link"]):
        tag.decompose()
        
    # Get text or simplified structure? 
    # For navigation, we need links. For extraction, we need structure.
    # Let's clean attributes but keep structure.
    
    for tag in soup.find_all(True):
        # Keep only href and src for img
        allowed_attrs = ['href', 'src', 'class', 'id']
        attrs = dict(tag.attrs)
        for attr in attrs:
            if attr not in allowed_attrs:
                del tag.attrs[attr]
                
    # Truncate if still huge? Flash handles 1M tokens, but let's be reasonable.
    # Just body is usually enough
    body = soup.find("body")
    if body:
        return str(body)[:100000] # Limit to 100k chars to be safe/fast
    return str(soup)[:100000]

def find_listing_url(html: str, base_url: str) -> str:
    """
    Asks LLM to find the best link pointing to 'Real Estate' (Imóveis) or 'Auctions' (Leilões).
    """
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""
    You are a crawler. I will provide the HTML of an auctioneer's homepage.
    Your goal is to find the URL that most likely leads to a list of REAL ESTATE (Imóveis) auctions or general auctions if specific category isn't clear.
    
    Base URL: {base_url}
    
    Rules:
    1. Look for keywords like "Imóveis", "Leilões", "Lotes", "Bens", "Agenda".
    2. Prefer "Imóveis" if available.
    3. Return ONLY a JSON object with a single key "url".
    4. If the URL is relative, assume it's relative to the Base URL, but return the string as found in href.
    5. If no suitable link is found, return {{"url": null}}.

    HTML Snippet:
    {html[:50000]}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        data = json.loads(response.text)
        link = data.get("url")
        
        if link:
            # Normalize URL
            if link.startswith("http"):
                return link
            elif link.startswith("/"):
                return base_url.rstrip("/") + link
            else:
                return base_url.rstrip("/") + "/" + link
        return None
    except Exception as e:
        print(f"LLM Navigation Error: {e}")
        return None

def extract_items(html: str, source_url: str) -> List[Dict]:
    """
    Asks LLM to extract auction items from the listing page.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""
    Extract a list of real estate auction items from this HTML.
    
    Source URL: {source_url}

    For each item, extract:
    - title: Short description/title of the property.
    - description: More details if available (location, size).
    - valuation: The appraisal value (Avaliação) if present.
    - minimum_bid: Minimum bid (Lance inicial/mínimo) if present.
    - status: "Open", "Closed", "Suspended" etc.
    - link: URL to the specific item details.
    
    Return a JSON object with a key "items" containing a list of objects.
    If no items found, return {{"items": []}}.
    
    HTML:
    {html[:60000]}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        data = json.loads(response.text)
        items = data.get("items", [])
        
        # Normalize item links
        for item in items:
            link = item.get("link")
            if link and not link.startswith("http"):
                base = "/".join(source_url.split("/")[:3]) # simple base extraction
                if link.startswith("/"):
                    item["link"] = base + link
                else:
                    item["link"] = base + "/" + link
                    
        return items
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        return []

def run_pipeline(limit: int = 10, offset: int = 0):
    if not setup_environment():
        return

    # Load sites
    sites = []
    if os.path.exists(SITES_FILE):
        with open(SITES_FILE, "r") as f:
            sites = [line.strip() for line in f if line.strip().startswith("http")]
    
    # Simple limit
    sites_to_crawl = sites[offset:offset+limit]
    
    all_extracted_items = []
    
    print(f"Starting crawl for {len(sites_to_crawl)} sites (offset {offset})...")
    
    for i, site_url in enumerate(sites_to_crawl):
        print(f"\n[{i+1}/{len(sites_to_crawl)}] Analyzing {site_url} ...")
        
        # 1. Fetch Homepage
        home_html = fetch_html(site_url)
        if not home_html:
            continue
            
        simple_home = simplify_html(home_html)
        
        # 2. Find Listing Page
        listing_url = find_listing_url(simple_home, site_url)
        if listing_url:
            print(f"  -> Found listing page: {listing_url}")
            
            # Avoid re-fetching if listing page is same as home (SPA or one-pager)
            if listing_url == site_url:
                listing_html = home_html
            else:
                listing_html = fetch_html(listing_url)
            
            if listing_html:
                simple_listing = simplify_html(listing_html)
                
                # 3. Extract Items
                items = extract_items(simple_listing, listing_url)
                if items:
                    print(f"  -> Extracted {len(items)} items.")
                    for item in items:
                        item["source_site"] = site_url
                        all_extracted_items.append(item)
                else:
                    print("  -> No items found on listing page.")
            else:
                print("  -> Failed to fetch listing page.")
        else:
            print("  -> Could not determine listing URL. Attempting extraction on homepage...")
            # Fallback: Try extracting from homepage
            items = extract_items(simple_home, site_url)
            if items:
                print(f"  -> Extracted {len(items)} items from homepage.")
                for item in items:
                    item["source_site"] = site_url
                    all_extracted_items.append(item)
            else:
                print("  -> No items found on homepage.")

        # Rate limit/politeness
        time.sleep(1)

    # Save Results
    if all_extracted_items:
        # Append if exists? For now assume valid JSON or overwrite
        existing = []
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        
        existing.extend(all_extracted_items)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=4)
        
        print(f"\nSaved total {len(existing)} items to {OUTPUT_FILE}")
    else:
        print("\nNo items extracted in this run.")
