from web3 import Web3
from django.conf import settings
import json

def get_contract_instance(address=None):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
    # Load your contract ABI
    with open(settings.CONTRACT_ABI_PATH) as f:
        contract_abi = json.load(f)
    
    if address:
        # If address is provided, return instance of deployed contract
        return w3.eth.contract(address=address, abi=contract_abi)
    else:
        # If no address, return contract class for deployment
        with open(settings.CONTRACT_BYTECODE_PATH) as f:
            contract_bytecode = f.read().strip()
        return w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

def deploy_smart_contract(oracle_address):
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    
    Contract = get_contract_instance()

    # Deploy contract
    tx_hash = Contract.constructor(oracle_address).transact({'from': w3.eth.accounts[0]})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_receipt.contractAddress

def add_transaction(contract_address, transaction_id, parcel_id, amount, terms_hash):
    contract = get_contract_instance(contract_address)
    
    tx_hash = contract.functions.addTransaction(
        transaction_id,
        parcel_id,
        int(amount * 100),  # Convert to cents
        Web3.keccak(text=terms_hash)
    ).transact({'from': Web3.eth.accounts[0]})
    
    tx_receipt = Web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt

def verify_payment(contract_address, transaction_id, amount, terms_hash):
    contract = get_contract_instance(contract_address)
    
    tx_hash = contract.functions.verifyPayment(
        transaction_id,
        int(amount * 100),  # Convert to cents
        Web3.keccak(text=terms_hash)
    ).transact({'from': settings.ORACLE_ADDRESS})
    
    tx_receipt = Web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt

def is_payment_verified(contract_address, transaction_id):
    contract = get_contract_instance(contract_address)
    return contract.functions.isPaymentVerified(transaction_id).call()

def get_transaction_terms_hash(contract_address, transaction_id):
    contract = get_contract_instance(contract_address)
    return contract.functions.getTransactionTermsHash(transaction_id).call()