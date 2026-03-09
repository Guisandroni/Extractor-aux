import pandas as pd
import re

def clean_url(url):
    """
    Cleans and validates a URL string.
    """
    if not isinstance(url, str):
        return ""
    
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
    
    # Basic validation
    if len(url) < 10 or not url.startswith("http"):
        return ""
        
    return url

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
