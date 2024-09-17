from web3 import Web3
from django.conf import settings
import json

def get_contract_instance(address=None):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
    with open(settings.CONTRACT_ABI_PATH) as f:
        contract_abi = json.load(f)
    
    if address:
        return w3.eth.contract(address=address, abi=contract_abi)
    else:
        with open(settings.CONTRACT_BYTECODE_PATH) as f:
            contract_bytecode = f.read().strip()
        return w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

def deploy_smart_contract(oracle_address):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
    Contract = get_contract_instance()
    
    try:
        tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.contractAddress
    except Exception as e:
        print(f"Error deploying contract: {str(e)}")
        return None

def add_transaction_part1(contract_address, agreement_id, total_amount, down_payment, penalty_rate):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    contract = get_contract_instance(contract_address)
    
    try:
        tx_hash = contract.functions.addTransactionPart1(
            agreement_id,
            total_amount,
            down_payment,
            penalty_rate
        ).transact({'from': w3.eth.accounts[0]})
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt
    except Exception as e:
        print(f"Error adding transaction part 1: {str(e)}")
        return None

def add_transaction_part2(contract_address, agreement_id, terms_hash, expiration_date, total_installments, cancellation_fee, refund_fee):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    contract = get_contract_instance(contract_address)
    
    try:
        tx_hash = contract.functions.addTransactionPart2(
            agreement_id,
            terms_hash,
            expiration_date,
            total_installments,
            cancellation_fee,
            refund_fee
        ).transact({'from': w3.eth.accounts[0]})
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt
    except Exception as e:
        print(f"Error adding transaction part 2: {str(e)}")
        return None

def verify_payment(contract_address, agreement_id, amount, terms_hash):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    contract = get_contract_instance(contract_address)
    
    try:
        tx_hash = contract.functions.verifyPayment(
            agreement_id,
            amount,
            terms_hash
        ).transact({'from': settings.ORACLE_ADDRESS})
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt
    except Exception as e:
        print(f"Error verifying payment: {str(e)}")
        return None

def is_payment_verified(contract_address, agreement_id):
    contract = get_contract_instance(contract_address)
    try:
        return contract.functions.isPaymentVerified(agreement_id).call()
    except Exception as e:
        print(f"Error checking payment verification: {str(e)}")
        return False

def get_transaction_details(contract_address, agreement_id):
    contract = get_contract_instance(contract_address)
    try:
        return contract.functions.getTransactionDetails(agreement_id).call()
    except Exception as e:
        print(f"Error getting transaction details: {str(e)}")
        return None






























# # smart_contract_manager.py

# from web3 import Web3
# from django.conf import settings
# import json

# def get_contract_instance(address=None):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
#     with open(settings.CONTRACT_ABI_PATH) as f:
#         contract_abi = json.load(f)
    
#     if address:
#         return w3.eth.contract(address=address, abi=contract_abi)
#     else:
#         with open(settings.CONTRACT_BYTECODE_PATH) as f:
#             contract_bytecode = f.read().strip()
#         return w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

# def deploy_smart_contract(oracle_address):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
#     Contract = get_contract_instance()
    
#     try:
#         tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
#         tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#         return tx_receipt.contractAddress
#     except Exception as e:
#         print(f"Error deploying contract: {str(e)}")
#         return None

# def add_transaction(contract_address, transaction_id, parcel_id, amount, terms_hash):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#     contract = get_contract_instance(contract_address)
    
#     try:
#         tx_hash = contract.functions.addTransaction(
#             transaction_id,
#             parcel_id,
#             int(amount * 100),  # Convert to smallest unit if necessary
#             Web3.keccak(text=terms_hash)
#         ).transact({'from': w3.eth.accounts[0]})  
        
#         tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#         return tx_receipt
#     except Exception as e:
#         print(f"Error adding transaction: {str(e)}")
#         return None

# def verify_payment(contract_address, transaction_id, amount, terms_hash):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#     contract = get_contract_instance(contract_address)
    
#     try:
#         tx_hash = contract.functions.verifyPayment(
#             transaction_id,
#             int(amount * 100),  # Convert to smallest unit if necessary
#             Web3.keccak(text=terms_hash)
#         ).transact({'from': settings.ORACLE_ADDRESS})
        
#         tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#         return tx_receipt
#     except Exception as e:
#         print(f"Error verifying payment: {str(e)}")
#         return None

# def is_payment_verified(contract_address, transaction_id):
#     contract = get_contract_instance(contract_address)
#     try:
#         return contract.functions.isPaymentVerified(transaction_id).call()
#     except Exception as e:
#         print(f"Error checking payment verification: {str(e)}")
#         return False

# def get_transaction_terms_hash(contract_address, transaction_id):
#     contract = get_contract_instance(contract_address)
#     try:
#         return contract.functions.getTransactionTermsHash(transaction_id).call()
#     except Exception as e:
#         print(f"Error getting transaction terms hash: {str(e)}")
#         return None













































# # smart_contract_manager.py

# from web3 import Web3
# from django.conf import settings
# import json

# def get_contract_instance(address=None):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
#     with open(settings.CONTRACT_ABI_PATH) as f:
#         contract_abi = json.load(f)
    
#     if address:
#         return w3.eth.contract(address=address, abi=contract_abi)
#     else:
#         with open(settings.CONTRACT_BYTECODE_PATH) as f:
#             contract_bytecode = f.read().strip()
#         return w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

# # def deploy_smart_contract(oracle_address):
# #     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
# #     Contract = get_contract_instance()
    
# #     tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
# #     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
# #     return tx_receipt.contractAddress
# def deploy_smart_contract(oracle_address):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
#     Contract = get_contract_instance()
    
#     try:
#         tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
#         tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#         return tx_receipt.contractAddress
#     except Exception as e:
#         print(f"Error deploying contract: {str(e)}")
#         return None




























# from web3 import Web3
# from django.conf import settings
# import json

# def get_contract_instance(address=None):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
   
#     with open(settings.CONTRACT_ABI_PATH) as f:
#         contract_abi = json.load(f)
    
#     if address:
      
#         return w3.eth.contract(address=address, abi=contract_abi)
#     else:
       
#         with open(settings.CONTRACT_BYTECODE_PATH) as f:
#             contract_bytecode = f.read().strip()
#         return w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

# def deploy_smart_contract(oracle_address):
#     w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
#     Contract = get_contract_instance()

  
#     tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
#     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
#     return tx_receipt.contractAddress

# def add_transaction(contract_address, transaction_id, parcel_id, amount, terms_hash):
#     contract = get_contract_instance(contract_address)
    
#     tx_hash = contract.functions.addTransaction(
#         transaction_id,
#         parcel_id,
#         int(amount * 100),  
#         Web3.keccak(text=terms_hash)
#     ).transact({'from': Web3.eth.accounts[0]})
    
#     tx_receipt = Web3.eth.wait_for_transaction_receipt(tx_hash)
#     return tx_receipt

# def verify_payment(contract_address, transaction_id, amount, terms_hash):
#     contract = get_contract_instance(contract_address)
    
#     tx_hash = contract.functions.verifyPayment(
#         transaction_id,
#         int(amount * 100),  
#         Web3.keccak(text=terms_hash)
#     ).transact({'from': settings.ORACLE_ADDRESS})
    
#     tx_receipt = Web3.eth.wait_for_transaction_receipt(tx_hash)
#     return tx_receipt

# def is_payment_verified(contract_address, transaction_id):
#     contract = get_contract_instance(contract_address)
#     return contract.functions.isPaymentVerified(transaction_id).call()

# def get_transaction_terms_hash(contract_address, transaction_id):
#     contract = get_contract_instance(contract_address)
#     return contract.functions.getTransactionTermsHash(transaction_id).call()