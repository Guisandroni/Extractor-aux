import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://www.innlei.org.br/leiloeiros-do-brasil"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def decode_cf_email(cf_string):
    """
    Decodes Cloudflare email protection string.
    """
    if not cf_string:
        return ""
    try:
        r = int(cf_string[:2], 16)
        email = ''.join([chr(int(cf_string[i:i+2], 16) ^ r) for i in range(2, len(cf_string), 2)])
        return email
    except (ValueError, IndexError):
        return ""

def fetch_page(page_num: int):
    """
    Fetch HTML for a given page of results.
    Assumes pagination uses ?page= query parameter.
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
        print(f"    [!] Error fetching detail {full_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Logic to find the Website in the detail page
    # Structure: 
    # <ul class="list-infos">
    #   <li>
    #     <strong>Site:</strong>
    #     <span><a href="...">...</a></span>
    #   </li>
    # </ul>
    
    new_website = None
    
    # Find all 'strong' tags and check if they contain "Site:"
    strongs = soup.find_all("strong")
    for strong in strongs:
        if "Site" in strong.get_text(strip=True):
            # The sibling/parent structure might vary, but usually it's in the same 'li'
            # Let's look for the 'a' tag in the parent 'li'
            parent_li = strong.find_parent("li")
            if parent_li:
                link = parent_li.find("a", href=True)
                if link:
                    href = link["href"].strip()
                    # Filter out placeholders or invalid links if necessary
                    if href and not href.endswith("email-protection"):
                        new_website = href
                        break
    
    return new_website

def main():
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
            # Check if website is empty or just "https://"
            current_site = entry.get("website", "")
            if not current_site or current_site == "https://":
                print(f"  -> Missing website for {entry['name']}. Checking profile...")
                enrich_site = get_detail_info(entry['profile_link'])
                if enrich_site:
                    print(f"     [+] Found: {enrich_site}")
                    entry['website'] = enrich_site
                else:
                    print("     [-] Not found in detail.")
                
                # Sleep briefly to be polite to the server
                time.sleep(0.5)

        all_leiloeiros.extend(entries)
        print(f" → Extracted {len(entries)} entries.")

        # Pagination check: Look for a link to the next page
        soup = BeautifulSoup(html, "html.parser")
        # We look for an <a> tag specifically pointing to the next page number
        next_page_str = f"page={page + 1}"
        next_link = soup.find("a", href=lambda href: href and next_page_str in href)
        
        if not next_link:
            print(f"No link found for page {page + 1}. Stopping.")
            break

        page += 1
        time.sleep(1)

    # Save to CSV
    df = pd.DataFrame(all_leiloeiros)
    df.to_csv("results/leiloeiros_innlei.csv", index=False, encoding="utf-8")
    print("Done! Saved to results/leiloeiros_innlei.csv")

if __name__ == "__main__":
    main()