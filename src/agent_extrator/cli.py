import argparse
import sys
import os
from pathlib import Path
from .agent_extrator_imoveis import execute_analysis
def main():
    parser = argparse.ArgumentParser(description="AI Auction Extrator CLI")
    parser.add_argument("--extract", action="store_true", help="Run the AI extraction agent on auction PDF notices.")
    parser.add_argument("--pdfs-dir", type=str, default="results/editais_pdfs", help="Directory where the source PDFs are located.")
    parser.add_argument("--output", type=str, default="results/categorized_properties.json", help="Path to save the resulting JSON file.")
    args = parser.parse_args()
    if args.extract:
        pdf_dir = Path(os.getcwd()) / args.pdfs_dir
        output_file = Path(os.getcwd()) / args.output
        os.makedirs(output_file.parent, exist_ok=True)
        print(f"Running Extrator Pipeline on directory: {pdf_dir}...")
        execute_analysis(str(pdf_dir), str(output_file))
    else:
        parser.print_help()
        sys.exit(1)
if __name__ == "__main__":
    main()
