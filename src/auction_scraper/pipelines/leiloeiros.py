import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from ..utils.common import decode_cf_email, clean_url

BASE_URL = "https://www.innlei.org.br/leiloeiros-do-brasil"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def fetch_page(page_num: int):
    """
    Fetch HTML for a given page of results.
    """
    params = {"page": page_num}
    response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
    response.raise_for_status()
    return response.text

def parse_leiloeiros(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    # Iterate over each article entry
    articles = soup.find_all("article")
    
    for article in articles:
        # Full Name & Profile Link
        h4_a = article.select_one(".cont-infos h4 a")
        name = h4_a.get_text(strip=True) if h4_a else ""
        profile_link = h4_a.get("href", "").strip() if h4_a else ""

        # Avatar
        img_tag = article.select_one(".cont-avatar img")
        avatar_url = img_tag.get("src", "").strip() if img_tag else ""

        # Description
        desc_div = article.select_one(".cont-infos .p-desc")
        description = desc_div.get_text(strip=True) if desc_div else ""

        # Website
        website_a = article.select_one(".show-website a")
        website = website_a.get("href", "").strip() if website_a else ""
        
        # Email (Cloudflare protected)
        email = ""
        email_a = article.select_one(".ul-social li a[href^='/cdn-cgi/l/email-protection']")
        if email_a:
            href = email_a.get("href", "")
            if "#" in href:
                cf_code = href.split("#")[-1]
                email = decode_cf_email(cf_code)

        items.append({
            "name": name,
            "profile_link": profile_link,
            "avatar_url": avatar_url,
            "description": description,
            "website": website,
            "email": email
        })

    return items

def get_detail_info(profile_rel_url: str):
    """
    Fetches the detail page and attempts to find a website link.
    """
    if not profile_rel_url:
        return None

    full_url = f"https://www.innlei.org.br{profile_rel_url}" if profile_rel_url.startswith("/") else profile_rel_url
    
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        # Silently fail or log debug
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    new_website = None
    
    strongs = soup.find_all("strong")
    for strong in strongs:
        if "Site" in strong.get_text(strip=True):
            parent_li = strong.find_parent("li")
            if parent_li:
                link = parent_li.find("a", href=True)
                if link:
                    href = link["href"].strip()
                    if href and not href.endswith("email-protection"):
                        new_website = href
                        break
    
    return new_website

def run_pipeline():
    print("Starting Leiloeiros Pipeline...")
    all_leiloeiros = []
    page = 1

    while True:
        print(f"Fetching page {page} ...")
        try:
            html = fetch_page(page)
        except Exception as e:
            print("Failed to fetch page:", e)
            break

        entries = parse_leiloeiros(html)
        if not entries:
            print("No entries found — likely last page.")
            break

        # Enrich data if website is missing
        for entry in entries:
            current_site = entry.get("website", "")
            if not current_site or current_site == "https://":
                enrich_site = get_detail_info(entry['profile_link'])
                if enrich_site:
                    entry['website'] = enrich_site
                
                time.sleep(0.2)

        all_leiloeiros.extend(entries)
        print(f" → Extracted {len(entries)} entries.")

        soup = BeautifulSoup(html, "html.parser")
        next_page_str = f"page={page + 1}"
        next_link = soup.find("a", href=lambda href: href and next_page_str in href)
        
        if not next_link:
            print(f"No link found for page {page + 1}. Stopping.")
            break

        page += 1
        time.sleep(1)

    # Save to CSV
    df = pd.DataFrame(all_leiloeiros)
    df.to_csv("leiloeiros_innlei.csv", index=False, encoding="utf-8")
    print("Done! Saved to leiloeiros_innlei.csv")
    
    # Run cleanup logic immediately
    print("Cleaning dataset...")
    df['website'] = df['website'].apply(clean_url)
    df.to_csv("leiloeiros_innlei_clean.csv", index=False)
    
    sites = df['website'].dropna().unique()
    sites = [s for s in sites if s and s.startswith("http")]
    sites.sort()

    with open("sites_de_leilao.txt", "w") as f:
        for site in sites:
            f.write(site + "\n")
            
    print(f"Extraction complete. Found {len(sites)} unique websites.")
