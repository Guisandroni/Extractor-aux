# AI Auction Extrator

This project is an AI-driven tool designed to extract structured data from real estate auction notices (Editais de Leilão) in PDF format. It uses Large Language Models (LLMs) to read, analyze, and categorize the assets listed in the documents.

## Features

- **Text Extraction**: Reads standard PDF documents to extract the content of auction notices.
- **OCR Fallback for Scanned PDFs**: Automatically detects PDFs that are scanned images (low extractable text) and uses **Google Gemini Vision** to extract the text reliably.
- **Structured Data Extraction**: Employs **LangChain** and **Gemini 2.5 Flash** to intelligently extract and categorize assets, returning a standardized JSON output.
- **Categorized Classification**: Separates extracted items into distinct categories: `houses`, `land`, `real_estate`, `vehicles`, and `others`. Each item includes details such as description, type, location, appraisal value, and minimum bid.

## Directory Structure

- **`src/agent_extrator/`**: Contains the source code for the AI extraction agent and CLI.
- **`results/editais_pdfs/`**: Default directory where source PDF notices should be placed.
- **`results/`**: Stores the output JSON file containing the extracted and categorized properties.

## Installation

1. Clone the repository and navigate to the project root.
2. Create and activate a Python virtual environment.
3. Install the package and its dependencies:

```bash
pip install -e .
```

4. Create a `.env` file in the root directory and add your Google API Key:

```env
GOOGLE_API_KEY="your_google_api_key_here"
```

*(Note: The codebase uses Google Gemini 2.5 Flash by default, but it can optionally be adapted to use Groq if desired by editing the agent initialization).*

## Usage

Place your auction notice PDFs in the `results/editais_pdfs` directory (or specify a custom directory).

Run the extraction agent using the installed CLI tool:

```bash
extract --extract
```

### CLI Options

The `extract` command supports the following arguments:

- `--extract`: Run the AI extraction agent on auction PDF notices.
- `--pdfs-dir`: Directory where the source PDFs are located (default: `results/editais_pdfs`).
- `--output`: Path to save the resulting JSON database (default: `results/categorized_properties.json`).

Example with custom paths:

```bash
extract --extract --pdfs-dir /path/to/my/pdfs --output /path/to/output.json
```
