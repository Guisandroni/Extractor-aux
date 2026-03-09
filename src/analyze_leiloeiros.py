import pandas as pd
import re
from collections import Counter

def analyze_data(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print("--- Data Analysis Report: leiloeiros_innlei.csv ---\n")

    # 1. Basic Counts
    total_records = len(df)
    print(f"Total Auctioneers: {total_records}")

    # 2. Missing Values
    print("\n[Missing Values]")
    print(df.isnull().sum())
    
    # 3. Contact Info Stats
    has_website = df['website'].notna() & (df['website'] != '')
    has_email = df['email'].notna() & (df['email'] != '')
    
    print("\n[Contact Information]")
    print(f"With Website: {has_website.sum()} ({has_website.sum()/total_records:.1%})")
    print(f"With Email:   {has_email.sum()} ({has_email.sum()/total_records:.1%})")

    # 4. State Distribution (Extracting from 'description')
    # The description column often contains strings like "JUCESP, JUCEMG"
    # We will extract all occurences of "JUC..." 
    
    state_counts = Counter()
    
    # Regex to find words starting with JUC followed by letters
    # This covers JUCESP, JUCEMG, JUCISRS, etc.
    junta_pattern = re.compile(r'(JUC[A-Z]+)')

    for desc in df['description'].dropna():
        matches = junta_pattern.findall(str(desc).upper())
        state_counts.update(matches)

    print("\n[Registration by State (Junta Comercial)]")
    if state_counts:
        # Convert to DataFrame for nice printing
        states_df = pd.DataFrame.from_dict(state_counts, orient='index', columns=['Count'])
        states_df = states_df.sort_values(by='Count', ascending=False)
        print(states_df)
    else:
        print("No state data found in 'description' column.")

    # 5. Email Domains (Simple check)
    print("\n[Top 5 Email Domains]")
    domains = []
    for email in df['email'].dropna():
        if '@' in str(email):
            parts = str(email).split('@')
            if len(parts) > 1:
                # Handle cases with multiple emails separated by space/comma
                # The scraper seemed to handle one, but let's be safe if data is dirty
                domain = parts[-1].strip().lower().split(' ')[0] 
                domains.append(domain)
    
    domain_counts = Counter(domains).most_common(5)
    for domain, count in domain_counts:
        print(f"{domain}: {count}")

if __name__ == "__main__":
    analyze_data("leiloeiros_innlei.csv")
