import argparse
import sys
from .pipelines import editais
from .pipelines import leiloeiros
from .pipelines import items_crawler

def main():
    parser = argparse.ArgumentParser(description="Auction Scraper CLI")
    parser.add_argument("--editais", action="store_true", help="Run the pipeline to scrape and extract auction notices (editais).")
    parser.add_argument("--leiloeiros", action="store_true", help="Run the pipeline to scrape auctioneer profiles and websites.")
    parser.add_argument("--items", action="store_true", help="Run the pipeline to crawl and extract real estate items from auctioneer sites using LLM.")
    parser.add_argument("--limit", type=int, default=10, help="Limit the number of sites/items to process (default: 10).")
    parser.add_argument("--offset", type=int, default=0, help="Offset to start processing from (default: 0).")

    args = parser.parse_args()

    if args.editais:
        print("Running Editais Pipeline...")
        # You can adjust default limits here or add more args
        editais.run_pipeline(do_scrape=True, do_extract=True, limit=args.limit)
        
    elif args.leiloeiros:
        print("Running Leiloeiros Pipeline...")
        leiloeiros.run_pipeline()
        
    elif args.items:
        print("Running Real Estate Items Pipeline...")
        items_crawler.run_pipeline(limit=args.limit, offset=args.offset)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
