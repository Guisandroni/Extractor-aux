import pandas as pd
import re

def clean_url(url):
    if not isinstance(url, str):
        return url
    
    # Remove common HTML dirt from end
    url = url.replace('">', '').replace('"', '').strip()
    
    # Remove spaces
    url = url.replace(" ", "")
    
    # Fix protocol typos
    url = url.replace("http://https://", "https://")
    url = url.replace("https://http://", "https://")
    url = url.replace("http://http://", "http://")
    url = url.replace("https://https://", "https://")
    
    # Fix starting dot typo (e.g. https://.site -> https://site)
    url = url.replace('https://.', 'https://').replace('http://.', 'http://')
    
    # Ensure it's still a valid-ish URL
    if len(url) < 10:
        return ""
        
    return url

df = pd.read_csv("leiloeiros_innlei.csv")
df['website'] = df['website'].apply(clean_url)

# Save cleaned CSV
df.to_csv("leiloeiros_innlei_clean.csv", index=False)

# Save unique sites
sites = df['website'].dropna().unique()
sites = [s for s in sites if s and s.startswith("http")]
sites.sort()

with open("sites_de_leilao.txt", "w") as f:
    for site in sites:
        f.write(site + "\n")

print(f"Cleaned {len(sites)} unique sites.")
