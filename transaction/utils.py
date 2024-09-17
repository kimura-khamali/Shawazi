import json
from django.conf import settings
from web3 import Web3
from PIL import Image
import pytesseract

def load_contract_abi():
    with open(settings.CONTRACT_ABI_PATH) as f:
        contract_abi = json.load(f)
    return contract_abi

def deploy_smart_contract(oracle_address):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))

    with open(settings.CONTRACT_BYTECODE_PATH) as f:
        contract_bytecode = f.read().strip()

    Contract = w3.eth.contract(abi=load_contract_abi(), bytecode=contract_bytecode)
    tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt.contractAddress

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise ValueError(f"Error extracting text from image: {e}")

def parse_transaction_data(text):
    """
    Parses transaction details from extracted text.
    Assumes a specific format of the text.
    """
    try:
        data = json.loads(text)
        return {
            'total_amount': data.get('total_amount'),
            'terms': data.get('terms'),
            'parcel_id': data.get('parcel_id'),
            'buyer': data.get('buyer'),
            'seller': data.get('seller')
        }
    except json.JSONDecodeError:
        raise ValueError("Error parsing transaction data from text")









# # transaction/utils.py

# import json
# from django.conf import settings

# def load_contract_abi():
#     with open(settings.CONTRACT_ABI_PATH) as f:
#         contract_abi = json.load(f)
#     return contract_abi

# def deploy_smart_contract(oracle_address):
#     from web3 import Web3
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))

#     with open(settings.CONTRACT_BYTECODE_PATH) as f:
#         contract_bytecode = f.read().strip()

#     Contract = w3.eth.contract(abi=load_contract_abi(), bytecode=contract_bytecode)
#     tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
#     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#     return tx_receipt.contractAddress














































# transaction/utils.py

# import json
# from web3 import Web3
# from django.conf import settings

# def deploy_smart_contract():
#     # Assuming you have a compiled contract artifact in JSON format
#     with open('path/to/compiled_contract.json') as f:
#         contract_json = json.load(f)
#     abi = contract_json['abi']
#     bytecode = contract_json['bytecode']

#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#     w3.eth.default_account = w3.eth.accounts[0]

#     Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
#     tx_hash = Contract.constructor().transact()
#     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#     return tx_receipt.contractAddress


















# import json
# import os
# from web3 import Web3

# def load_contract_abi(path):
#     if not os.path.isfile(path):
#         raise FileNotFoundError(f"ABI file not found at {path}")
    
#     with open(path, 'r') as abi_file:
#         try:
#             return json.load(abi_file)
#         except json.JSONDecodeError as e:
#             raise ValueError(f"Invalid JSON in ABI file at {path}: {e}")

# def load_contract_bytecode(path):
#     if not os.path.isfile(path):
#         raise FileNotFoundError(f"Bytecode file not found at {path}")
    
#     with open(path, 'r') as bytecode_file:
#         return bytecode_file.read().strip()

# def deploy_script():
    
#     w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    
   
#     abi = load_contract_abi('./path_to_abi.json')
#     bytecode = load_contract_bytecode('./path_to_bytecode.bin')
    
  
#     Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    
#     oracle_address = '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994'  
    
   
#     tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
#     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
   
#     return tx_receipt.contractAddress
