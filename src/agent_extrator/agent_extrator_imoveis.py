import os
import json
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
import fitz  
import base64
class Item(BaseModel):
    description: str = Field(description="Detailed description of the auctioned item/asset")
    type: Optional[str] = Field(description="Specific type (e.g., apartment, house, block, farm, car, truck, machinery)")
    location: Optional[str] = Field(description="Full address, city, state, or location of the item/property")
    appraisal_value: Optional[float] = Field(description="Monetary appraisal value of the item in BRL, if available")
    minimum_bid: Optional[float] = Field(description="Minimum or initial bid value in BRL, if available")
class ItemCategories(BaseModel):
    houses: List[Item] = Field(
        default=[], 
        description="List of ready-built residences: houses, apartments, townhouses, and condos."
    )
    land: List[Item] = Field(
        default=[], 
        description="List of unbuilt areas: land, lots, bare land tracts."
    )
    real_estate: List[Item] = Field(
        default=[], 
        description="Other types of real estate not covered by the previous categories: industrial warehouses, commercial rooms, farms with improvements, buildings, etc."
    )
    vehicles: List[Item] = Field(
        default=[], 
        description="List of vehicles: cars, motorcycles, trucks, buses, tractors, etc."
    )
    others: List[Item] = Field(
        default=[], 
        description="Any other auctioned goods: machinery, electronics, equipment, quotas, clothes, scrap, etc."
    )
def create_extractor_agent():
    """
    Creates the LangChain chain/agent responsible for reading the text and enforcing 
    the structured output in the requested categorization of houses, land, and real_estate.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_agent = llm.with_structured_output(ItemCategories)
    system_prompt = """You are an expert in legal analysis and asset surveying for auction notices (editais de leilões).
Your main mission is to read the provided auction notice text and intensively search for ALL assets and goods available for bidding.
Strictly follow these instructions:
1. CONDUCT A THOROUGH SEARCH FOR ASSETS: Do not let any property or good slip by. Extract real estate, lands, vehicles, machinery, and ANY other items listed.
2. STRUCTURED DATA EXTRACTION: For each item, extract the exact 'description' from the notice, try to identify its 'type', the clearest 'location' possible, its 'appraisal_value' (Avaliação), and 'minimum_bid' (Lance Inicial/Mínimo) in numeric format, without currency formatting, or null if not available.
3. CATEGORIZATION: You must strictly place each found asset into ONE, and only ONE, of the 5 lists below in the JSON format provided by the system:
   - "houses": Only fully constructed residences intended for direct habitation (houses, apartments, townhouses, penthouses).
   - "land": Any land area without significant residential/commercial improvements (lots, bare land, dry rural tracts, subdivisions).
   - "real_estate": Any other real estate assets (entire buildings, commercial rooms, warehouses, unseparated large farms, mixed rural properties).
   - "vehicles": Any type of vehicles (cars, motorcycles, trucks, buses, boats).
   - "others": Any other goods such as machinery, electronics, equipment, scrap, materials, etc.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Here is the content of the auction notice in text. Accomplish your task below:\n\nNOTICE CONTENT:\n{auction_text}")
    ])
    return prompt | structured_agent
def execute_analysis(pdf_directory: str, output_json_file: str):
    """
    Reads the PDFs, invokes the agent on each file, and saves the mapped attributes in JSON.
    """
    print(f"Loading PDF documents from '{pdf_directory}'...")
    try:
        loader = PyPDFDirectoryLoader(pdf_directory)
        documents = loader.load()
    except Exception as e:
        print(f"Error trying to load PDFs: {e}")
        return
    if not documents:
        print("No PDF documents found. Check if there are uncorrupted PDFs in the directory.")
    texts_by_file = {}
    for doc in documents:
        source = doc.metadata.get("source", "unknown_document.pdf")
        if source not in texts_by_file:
            texts_by_file[source] = ""
        texts_by_file[source] += doc.page_content + "\n\n"
    ocr_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    print("Checking for scanned PDFs that require OCR...")
    pdf_files = list(Path(pdf_directory).glob("*.pdf"))
    for pdf_path_obj in pdf_files:
        source_str = str(pdf_path_obj.resolve())
        current_text = texts_by_file.get(source_str, texts_by_file.get(str(pdf_path_obj), ""))
        if len(current_text.strip()) < 100:
            filename = pdf_path_obj.name
            print(f" -> '{filename}' has low/no extractable text. Running Cloud OCR with Gemini...")
            try:
                doc = fitz.open(str(pdf_path_obj))
                ocr_text = ""
                num_pages = min(5, len(doc))
                for page_num in range(num_pages):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    image_data = base64.b64encode(img_bytes).decode("utf-8")
                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": "Extract all text from this scanned document exactly as it appears. Return ONLY the text."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                        ]
                    )
                    response = ocr_llm.invoke([message])
                    if response and response.content:
                        ocr_text += response.content + "\n\n"
                texts_by_file[source_str] = ocr_text
                print(f"    [OCR] Extracted {len(ocr_text)} characters from {num_pages} pages using Gemini Vision.")
            except Exception as e:
                print(f"    [OCR Error] Failed to extract text from {filename}: {e}")
    agent = create_extractor_agent()
    final_results = {}
    print("\nStarting extraction with AI agent (LangChain / LLM)...")
    pdf_files_to_process = list(texts_by_file.items())[:6]
    for file, full_text in pdf_files_to_process:
        filename = Path(file).name
        print(f"-> Analyzing: {filename}")
        try:
            structured_result = agent.invoke({"auction_text": full_text})
            if hasattr(structured_result, 'model_dump'):
                final_results[filename] = structured_result.model_dump()
            else:
                final_results[filename] = structured_result.dict()
            n_houses = len(structured_result.houses)
            n_land = len(structured_result.land)
            n_real_estate = len(structured_result.real_estate)
            n_vehicles = len(structured_result.vehicles)
            n_others = len(structured_result.others)
            print(f"   [+] OK: {n_houses} houses | {n_land} land | {n_real_estate} real estate | {n_vehicles} vehicles | {n_others} others")
        except Exception as e:
            print(f"   [!] Error during analysis of {filename}: {e}")
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print(f"\nExtraction completed successfully! The categorized data was saved in: {output_json_file}")
if __name__ == "__main__":
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    PDFS_FOLDER = ROOT_DIR / "results" / "editais_pdfs"
    OUTPUT_JSON_FILE = ROOT_DIR / "results" / "categorized_properties.json"
    os.makedirs(OUTPUT_JSON_FILE.parent, exist_ok=True)
    execute_analysis(str(PDFS_FOLDER), str(OUTPUT_JSON_FILE))
