import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://www.innlei.org.br/editais"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def fetch_page(page_num: int):
    params = {"page": page_num}
    response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
    response.raise_for_status()
    return response.text

def parse_editais(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    
    # Locate the table body
    tbody = soup.find("tbody")
    if not tbody:
        return []
    
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
            
        # 1st TD is "Comitente" (Name)
        name = tds[0].get_text(strip=True)
        
        # Last TD (usually 3rd) contains the link
        # We look for the 'a' tag in the last column
        link_td = tds[-1]
        a_tag = link_td.find("a")
        
        url = ""
        if a_tag:
            url = a_tag.get("href", "").strip()
        
        items.append({"Edital Name": name, "File URL": url})
        
    return items

def main():
    all_editais = []
    page = 1
    
    while True:
        print(f"Fetching page {page} ...")
        try:
            html = fetch_page(page)
        except Exception as e:
            print(f"Failed to fetch page {page}: {e}")
            break
            
        entries = parse_editais(html)
        if not entries:
            print("No entries found — likely last page.")
            break
            
        all_editais.extend(entries)
        print(f" → Extracted {len(entries)} entries.")
        
        # Pagination check
        soup = BeautifulSoup(html, "html.parser")
        next_page_str = f"page={page + 1}"
        # Look for a link specifically pointing to the next page number
        next_link = soup.find("a", href=lambda href: href and next_page_str in href)
        
        if not next_link:
            print(f"No link found for page {page + 1}. Stopping.")
            break
            
        page += 1
        time.sleep(1)
        
    # Save to CSV
    df = pd.DataFrame(all_editais)
    df.to_csv("editais.csv", index=False, encoding="utf-8")
    print(f"Done! Saved {len(df)} editais to editais.csv")

if __name__ == "__main__":
    main()
