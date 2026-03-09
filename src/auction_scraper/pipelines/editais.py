import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import json
import pdfplumber
import google.generativeai as genai
from typing import List, Dict, Any

# Configuration
BASE_URL = "https://www.innlei.org.br/editais"
DOWNLOAD_DIR = "results/editais_pdfs"
OUTPUT_CSV = "aux/editais.csv"
OUTPUT_JSON = "results/editais_extracted.json"
MODEL_NAME = "gemini-2.0-flash"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def setup_environment():
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set.")
        return False
    genai.configure(api_key=api_key)
    return True

def fetch_page(page_num: int):
    params = {"page": page_num}
    response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
    response.raise_for_status()
    return response.text

def parse_editais(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    
    tbody = soup.find("tbody")
    if not tbody:
        return []
    
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
            
        name = tds[0].get_text(strip=True)
        link_td = tds[-1]
        a_tag = link_td.find("a")
        
        url = ""
        if a_tag:
            url = a_tag.get("href", "").strip()
        
        items.append({"Edital Name": name, "File URL": url})
        
    return items

def scrape_editais_list(max_pages=None):
    print("Starting Edital List Scraping...")
    all_editais = []
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
            
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
        
        soup = BeautifulSoup(html, "html.parser")
        next_page_str = f"page={page + 1}"
        next_link = soup.find("a", href=lambda href: href and next_page_str in href)
        
        if not next_link:
            print(f"No link found for page {page + 1}. Stopping.")
            break
            
        page += 1
        time.sleep(1)
        
    df = pd.DataFrame(all_editais)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"List saved to {OUTPUT_CSV} ({len(df)} records)")
    return df

def download_pdf(url: str, save_path: str) -> bool:
    if os.path.exists(save_path):
        return True
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def extract_text_from_pdf(pdf_path: str, max_pages: int = 5) -> str:
    text_content = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                text = page.extract_text()
                if text:
                    text_content.append(text)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return "\n".join(text_content)

def extract_info_with_llm(text: str, filename: str) -> Dict[str, Any]:
    if not text.strip():
        return None

    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""
    You are an expert legal document analyzer. Your task is to extract structured information from the following Brazilian "Edital de Leilão" (Auction Notice).
    
    Filename: {filename}    
    Extract the following fields and return ONLY a valid JSON object. Do not include markdown formatting like ```json ... ```.    
    Fields to extract:
    1. auction_type: "Judicial", "Extrajudicial", or "Unknown".
    2. judge: Object with "name" and "court".
    3. auctioneer: Object with "name" and "registration" (Matrícula/JUCESP number).
    4. address: The physical address mentioned for the auctioneer or place of auction.
    5. website: The auction website URL.
    6. legal_case: Object with "number" (Processo nº) and "type" (Ação/Classe).
    7. parties: Object with "plaintiff" (Exequente/Comitente) and "defendant" (Executado/Devedor).
    8. auction_dates: List of strings.
    9. contact: Phone numbers or emails.
    10. properties: A LIST of objects, where each object represents a lot/good (Lote/Bem) and contains:
        - raw_description: The full description text.
        - type: "Real Estate", "Vehicle", "Machinery", or "Other".
        - valuation: The appraisal value (Avaliação).
        - minimum_bid: The minimum bid amount (Lance Mínimo).
        - location: Location of the property.
        - depositary: Name of the depositary (Fiel Depositário).

    If a field is not found, use null.    
    Text content:
    {text[:30000]} 
    """

    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"LLM Extraction failed for {filename}: {e}")
        return None

def process_pdfs(limit=20):
    if not setup_environment():
        return

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    try:
        df = pd.read_csv(OUTPUT_CSV)
    except FileNotFoundError:
        print(f"File {OUTPUT_CSV} not found. Run scraper first.")
        return

    results = []
    
    # Filter for PDF files
    pdf_entries = df[df['File URL'].str.lower().str.endswith('.pdf', na=False)]
    
    if limit:
        pdf_entries = pdf_entries.head(limit)
    
    print(f"Processing {len(pdf_entries)} PDF files with {MODEL_NAME}...")

    for index, row in pdf_entries.iterrows():
        url = row['File URL']
        name = row['Edital Name']
        filename = url.split('/')[-1]
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        print(f"[{index+1}] {name}...")

        if download_pdf(url, filepath):
            text = extract_text_from_pdf(filepath)
            extracted_info = extract_info_with_llm(text, filename)
            
            if extracted_info:
                results.append({
                    "edital_name": name,
                    "file_url": url,
                    "extracted_data": extracted_info
                })
                time.sleep(1) 
            else:
                print("   -> Failed to extract info.")

    # Save results
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"Saved LLM extraction results to {OUTPUT_JSON}")

def run_pipeline(do_scrape=True, do_extract=True, limit=20):
    if do_scrape:
        scrape_editais_list()
    
    if do_extract:
        process_pdfs(limit=limit)
