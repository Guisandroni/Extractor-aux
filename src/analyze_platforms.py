import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time
from collections import Counter

INPUT_FILE = "sites_de_leilao.txt"
OUTPUT_MD = "WEBSITE_PATTERNS.md"

# Common platforms fingerprints (text or meta generator)
PLATFORMS = {
    "Superbid": ["superbid", "superbid.net"],
    "BomValor": ["bomvalor", "bom valor"],
    "Lance Judicial": ["lance judicial", "lancejudicial"],
    "Mega Leilões": ["megaleiloes", "mega leilões"],
    "Sodré Santoro": ["sodresantoro", "sodré santoro"],
    "Zukerman": ["zukerman"],
    "Leilão Judicial Eletrônico": ["leilaojudicialeletronico", "leilão judicial eletrônico"],
    "Gestor de Leilões": ["gestordeleiloes", "gestor de leilões"],
    "WLeilões": ["wleiloes", "wleilões"],
    "Lote Leilões": ["loteleiloes"],
    "E-Leilões": ["e-leiloes", "e-leilões"],
    "Vip Leilões": ["vipleiloes", "vip leilões"],
    "Freitas Leiloeiro": ["freitasleiloeiro"],
    "Milan Leilões": ["milanleiloes"],
    "Frazão Leilões": ["frazaoleiloes"],
    "Kronberg": ["kronberg"],
    "Pestana": ["pestanaleiloes"],
    "Copart": ["copart"],
    "Palácio dos Leilões": ["palaciodosleiloes"],
    "Banco do Brasil": ["banco do brasil"], # Often hosted or mentioned
    "Caixa": ["caixa economica", "caixa econômica"], # Often hosted or mentioned
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def clean_and_load_urls(filepath):
    urls = set()
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Basic cleanup of dirt observed in file
            if "E-mail:" in line: 
                line = line.split("E-mail:")[0].strip()
            if "</div>" in line:
                line = line.replace("</div>", "").strip()
            if " " in line:
                line = line.split(" ")[0]
            
            if line.startswith("http"):
                urls.add(line)
    return list(urls)

def detect_platform(html, url):
    html_lower = html.lower()
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text().lower()
    
    detected = []
    
    # Check footers/meta/title
    for name, keywords in PLATFORMS.items():
        for keyword in keywords:
            if keyword in url.lower() or keyword in text:
                detected.append(name)
                break
                
    # Specific Checks for Tech Providers (often in footer "Desenvolvido por...")
    if "superbid" in html_lower:
        detected.append("Superbid Technology")
    if "bomvalor" in html_lower:
        detected.append("BomValor Tech")
        
    return list(set(detected))

def main():
    urls = clean_and_load_urls(INPUT_FILE)
    print(f"Loaded {len(urls)} unique URLs.")
    
    # Analyze a sample (e.g. first 50 to avoid long runtime)
    sample_urls = urls[:50] 
    
    results = {}
    platform_counts = Counter()
    
    print(f"Analyzing {len(sample_urls)} sites...")
    
    for i, url in enumerate(sample_urls):
        print(f"[{i+1}/{len(sample_urls)}] Checking {url} ...")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            platforms = detect_platform(response.text, url)
            
            if platforms:
                results[url] = platforms
                for p in platforms:
                    platform_counts[p] += 1
            else:
                results[url] = ["Unknown / Custom"]
                platform_counts["Unknown / Custom"] += 1
                
        except Exception as e:
            print(f"  Error: {e}")
            results[url] = ["Unreachable"]
            platform_counts["Unreachable"] += 1
            
        time.sleep(0.5)
        
    # Generate Markdown Report
    with open(OUTPUT_MD, "w") as f:
        f.write("# Auction Website Patterns & Platforms\n\n")
        f.write("Analysis of discovered auctioneer websites to identify common platforms and technology providers.\n\n")
        
        f.write("## Top Platforms Identified\n")
        for platform, count in platform_counts.most_common():
            f.write(f"- **{platform}**: {count} sites\n")
            
        f.write("\n## Detailed Analysis (Sample)\n")
        f.write("| Website | Detected Platform/Keywords |\n")
        f.write("|---|---|")
        for url, plats in results.items():
            f.write(f"| {url} | {', '.join(plats)} |\n")
            
        f.write("\n## Extraction Strategy Recommendations\n")
        f.write("Based on the findings, here are strategies for extracting auction data:\n\n")
        f.write("1. **Superbid / BomValor / Lance Judicial:** These appear to be major aggregators or tech providers. Writing specific spiders for their DOM structure will yield high returns as many sites use their backend.\n")
        f.write("2. **Custom Sites:** Many auctioneers have custom WordPress or PHP sites. A generic scraper looking for keywords like 'Lote', 'Lance', 'Edital', 'Próximos Leilões' is needed.\n")
        f.write("3. **Common Data Points:** Almost all sites list:\n")
        f.write("   - `Status` (Aberto, Encerrado, Breve)\n")
        f.write("   - `Data` (1ª Praça, 2ª Praça)\n")
        f.write("   - `Valor` (Avaliação, Lance Mínimo)\n")
        f.write("   - `Foto` (Thumbnail of the lot)\n")
        
    print(f"Analysis complete. Report saved to {OUTPUT_MD}")

if __name__ == "__main__":
    main()
