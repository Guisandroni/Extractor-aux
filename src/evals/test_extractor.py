import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We can import the function from our extractor package
from agent_extrator.agent_extrator_imoveis import create_extractor_agent

def evaluate_extractor():
    """
    Introductory Evaluation Script for the AI Extractor.
    Tests the fundamental capability of the agent to structure a mock text
    into the desired Pydantic schemas (ItemCategories).
    """
    print("=== Starting Extractor Evaluation ===\n")
    
    # 1. Check for API Key
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GROQ_API_KEY"):
        print("[-] ERROR: No API key found. Please set GOOGLE_API_KEY or GROQ_API_KEY in your .env file.")
        return

    print("[+] API Key found.")
    
    # 2. Instantiate the agent
    print("[*] Instantiating the Langchain Agent...")
    try:
        agent = create_extractor_agent()
        print("[+] Agent instantiated successfully.")
    except Exception as e:
        print(f"[-] ERROR instantiating agent: {e}")
        return

    # 3. Create a mock auction notice text for evaluation
    mock_auction_text = """
    EDITAL DE LEILÃO ELETRÔNICO
    O Leiloeiro Oficial torna público que realizará leilão dos seguintes bens:
    
    Lote 01: Apartamento n. 42, situado na Rua das Flores, 123, Bairro Jardim Primavera, São Paulo/SP. 
    Avaliação: R$ 350.000,00. Lance Inicial: R$ 175.000,00.
    
    Lote 02: Terreno rural com área de 5 hectares, sem benfeitorias, localizado na Estrada do Sol, km 12, Zona Rural, Campinas/SP.
    Avaliação: R$ 120.000,00. Lance Inicial: R$ 60.000,00.
    
    Lote 03: Veículo Honda Civic, ano 2020, cor preta, placa ABC-1234.
    Avaliação: R$ 95.000,00. Lance Inicial: R$ 50.000,00.
    """

    print("\n[*] Running extraction on mock text...")
    print(f"--- Mock Text Snippet ---\n{mock_auction_text.strip()}\n-------------------------\n")
    
    # 4. Invoke the agent
    try:
        # Note: Depending on the implementation of create_extractor_agent, 
        # it might expect 'auction_text' as the input key dictionary.
        result = agent.invoke({"auction_text": mock_auction_text})
        
        # Determine how to dump the pydantic model based on the version
        if hasattr(result, 'model_dump'):
            parsed_data = result.model_dump()
        else:
            parsed_data = result.dict()
            
        print("[+] Extraction successful! JSON Output:\n")
        print(json.dumps(parsed_data, indent=4, ensure_ascii=False))
        
        # 5. Basic Assertions (The Evaluation core)
        print("\n[*] Evaluating the results...")
        
        assert len(parsed_data.get("houses", [])) == 1, "Expected 1 house/apartment"
        assert len(parsed_data.get("land", [])) == 1, "Expected 1 land property"
        assert len(parsed_data.get("vehicles", [])) == 1, "Expected 1 vehicle"
        
        # Validate that values got extracted somewhat correctly
        house = parsed_data["houses"][0]
        assert house["appraisal_value"] == 350000.0, "House appraisal value mismatch"
        assert house["minimum_bid"] == 175000.0, "House minimum bid mismatch"
        
        print("\n[+] All core evaluations PASSED! The structured JSON logic is working as expected.")
        
    except AssertionError as ae:
        print(f"\n[-] EVALUATION FAILED: {ae}")
    except Exception as e:
        print(f"\n[-] ERROR during execution/evaluation: {e}")

if __name__ == "__main__":
    evaluate_extractor()
