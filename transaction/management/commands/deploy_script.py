import os
import json
from django.core.management.base import BaseCommand
from web3 import Web3
from django.conf import settings
from transaction.models import Transaction

class Command(BaseCommand):
    help = 'Deploys the LandTransaction smart contract'

    def handle(self, *args, **options):
        # Connect to the blockchain provider
        w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

        # Ensure the connection is successful
        if not w3.is_connected():
            self.stdout.write(self.style.ERROR('Failed to connect to the blockchain provider'))
            return

        # Get the account to deploy from
        account = w3.eth.accounts[0]
        self.stdout.write(f'Using account: {account}')

        # Load contract ABI and bytecode
        contract_path = './transaction/artifacts/transaction/smart_contract/LandTransaction.sol/LandTransaction.json'
        
        try:
            with open(contract_path, 'r') as file:
                contract_json = json.load(file)
                contract_abi = contract_json['abi']
                contract_bytecode = contract_json['bytecode']
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Contract file not found at {contract_path}'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in contract file at {contract_path}'))
            return
        
        # Prepare contract instance
        LandTransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

        # Define constructor arguments
        oracle_address = '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994'  # Replace with your actual oracle address

        # Deploy the contract
        try:
            tx_hash = LandTransactionContract.constructor(oracle_address).transact({'from': account})
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get the contract address
            contract_address = tx_receipt.contractAddress
            self.stdout.write(self.style.SUCCESS(f'Contract deployed to {contract_address}'))

            # Update the contract address in the Django model
            Transaction.objects.update(smart_contract_address=contract_address)
            self.stdout.write(self.style.SUCCESS('Updated Transaction objects with new contract address'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error deploying contract: {str(e)}'))








# import json
# from django.core.management.base import BaseCommand
# from web3 import Web3
# from django.conf import settings
# from transaction.models import Transaction

# class Command(BaseCommand):
#     help = 'Deploys the LandTransaction smart contract'

#     def handle(self, *args, **options):
#         try:
#             # Connect to the blockchain provider
#             w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
            
#             # Ensure the connection is successful
#             if not w3.is_connected():
#                 self.stdout.write(self.style.ERROR('Failed to connect to the blockchain provider'))
#                 return

#             # Get the account to deploy from
#             account = w3.eth.accounts[0]
#             self.stdout.write(f'Using account: {account}')
            
#             # Load contract ABI and bytecode
#             contract_path = './transaction/artifacts/transaction/smart_contract/LandTransaction.sol/LandTransaction.json'
#             self.stdout.write(f'Loading contract from: {contract_path}')
            
#             with open(contract_path, 'r') as file:
#                 contract_json = json.load(file)
#                 contract_abi = contract_json['abi']
#                 contract_bytecode = contract_json['bytecode']
            
#             # Prepare contract instance
#             LandTransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
            
#             # Define constructor arguments
#             oracle_address = '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994'
            
#             # Deploy the contract
#             tx_hash = LandTransactionContract.constructor(oracle_address).transact({'from': account})
#             tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
#             # Get the contract address
#             contract_address = tx_receipt.contractAddress
#             self.stdout.write(self.style.SUCCESS(f'Contract deployed to {contract_address}'))
            
#             # Update the contract address in the Django model
#             Transaction.objects.update(smart_contract_address=contract_address)
#             self.stdout.write(self.style.SUCCESS('Updated Transaction objects with new contract address'))

#         except FileNotFoundError as e:
#             self.stdout.write(self.style.ERROR(f'File not found: {str(e)}'))
#         except Exception as e:
#             self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))



























# import json
# from django.core.management.base import BaseCommand
# from web3 import Web3
# from django.conf import settings
# from transaction.models import Transaction

# class Command(BaseCommand):
#     help = 'Deploys the LandTransaction smart contract'

#     def handle(self, *args, **options):
#         try:
#             # Connect to the blockchain provider
#             w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
            
#             # Ensure the connection is successful
#             if not w3.is_connected():
#                 self.stdout.write(self.style.ERROR('Failed to connect to the blockchain provider'))
#                 return

#             # Get the account to deploy from
#             account = w3.eth.accounts[0]
#             self.stdout.write(f'Using account: {account}')
            
#             # Load contract ABI and bytecode
#             with open('./transaction/artifacts/contracts/LandTransaction.sol/LandTransaction.json', 'r') as file:
#                 contract_json = json.load(file)
#                 contract_abi = contract_json['abi']
#                 contract_bytecode = contract_json['bytecode']
            
#             # Prepare contract instance
#             LandTransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
            
#             # Define constructor arguments
#             oracle_address = '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994'
            
#             # Deploy the contract
#             tx_hash = LandTransactionContract.constructor(oracle_address).transact({'from': account})
#             tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
#             # Get the contract address
#             contract_address = tx_receipt.contractAddress
#             self.stdout.write(self.style.SUCCESS(f'Contract deployed to {contract_address}'))
            
#             # Update the contract address in the Django model
#             Transaction.objects.update(smart_contract_address=contract_address)
#             self.stdout.write(self.style.SUCCESS('Updated Transaction objects with new contract address'))

#         except FileNotFoundError as e:
#             self.stdout.write(self.style.ERROR(f'File not found: {str(e)}'))
#         except Exception as e:
#             self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))







































# from django.core.management.base import BaseCommand
# from web3 import Web3
# from django.conf import settings
# from transaction.models import Transaction
# from transaction.utils import load_contract_abi, load_contract_bytecode

# class Command(BaseCommand):
#     help = 'Deploys the LandTransaction smart contract'

#     def handle(self, *args, **options):
#         try:
#             # Connect to the blockchain provider
#             w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
            
#             # Ensure the connection is successful
#             if not w3.is_connected():
#                 self.stdout.write(self.style.ERROR('Failed to connect to the blockchain provider'))
#                 return

#             # Get the account to deploy from
#             account = w3.eth.accounts[0]
#             self.stdout.write(f'Using account: {account}')
            
#             # Load contract ABI and bytecode
#             contract_abi = load_contract_abi('path/to/your/LandTransaction.abi')
#             contract_bytecode = load_contract_bytecode('path/to/your/LandTransaction.bin')
            
#             # Prepare contract instance
#             LandTransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
            
#             # Define constructor arguments
#             oracle_address = '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994'
            
#             # Deploy the contract
#             tx_hash = LandTransactionContract.constructor(oracle_address).transact({'from': account})
#             tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
#             # Get the contract address
#             contract_address = tx_receipt.contractAddress
#             self.stdout.write(self.style.SUCCESS(f'Contract deployed to {contract_address}'))
            
#             # Update the contract address in the Django model
#             Transaction.objects.update(smart_contract_address=contract_address)
#             self.stdout.write(self.style.SUCCESS('Updated Transaction objects with new contract address'))

#         except FileNotFoundError as e:
#             self.stdout.write(self.style.ERROR(f'File not found: {str(e)}'))
#         except Exception as e:
#             self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))






















# # deployment_script.py

# from django.core.management.base import BaseCommand
# from web3 import Web3
# from django.conf import settings
# from transaction.models import Transaction
# from transaction.utils import load_contract_abi

# class Command(BaseCommand):
#     help = 'Deploys the LandTransaction smart contract'

#     def handle(self, *args, **options):
#         # Connect to the blockchain provider
#         # w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#         w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        
#         # Ensure the connection is successful
#         if not w3.is_connected():
#             self.stdout.write(self.style.ERROR('Failed to connect to the blockchain provider'))
#             return

#         # Get the account to deploy from
#         account = w3.eth.accounts[0]
#         self.stdout.write(f'Using account: {account}')
        
#         # Load contract ABI and bytecode
#         contract_abi = load_contract_abi()
#         contract_bytecode = "0xC11D335a2C3977909eC2E8aBDfADE4AC84e4370C"  # Replace with your actual bytecode
        
#         # Prepare contract instance
#         LandTransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
        
#         # Define constructor arguments
#         oracle_address = '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994'
        
#         # Deploy the contract
#         tx_hash = LandTransactionContract.constructor(oracle_address).transact({'from': account})
#         tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
#         # Get the contract address
#         contract_address = tx_receipt.contractAddress
#         self.stdout.write(self.style.SUCCESS(f'Contract deployed to {contract_address}'))
        
#         # Update the contract address in the Django model
#         Transaction.objects.update(smart_contract_address=contract_address)




































# from django.core.management.base import BaseCommand
# from web3 import Web3
# import os
# from transactions.utils import load_contract_abi  # Assuming this utility loads the ABI
# from transactions.models import LandTransaction

# class Command(BaseCommand):
#     help = 'Deploys the LandTransaction smart contract'

#     def handle(self, *args, **options):
#         # Set up Web3 connection
#         blockchain_provider_url = os.getenv('BLOCKCHAIN_PROVIDER_URL')
#         w3 = Web3(Web3.HTTPProvider(blockchain_provider_url))
        
#         if not w3.isConnected():
#             self.stdout.write(self.style.ERROR('Failed to connect to the blockchain network'))
#             return

#         # Load account, contract bytecode, and ABI
#         account = w3.eth.accounts[0]
#         contract_abi = load_contract_abi()  # Load ABI from JSON file
#         contract_bytecode = os.getenv('SMART_CONTRACT_BYTECODE')  # Fetch bytecode from environment variables

#         # Set up smart contract instance
#         LandTransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
#         oracle_address = os.getenv('ORACLE_ADDRESS', '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994')

#         # Build and deploy the contract
#         transaction = LandTransactionContract.constructor(oracle_address).buildTransaction({
#             'from': account,
#             'gas': 2000000,
#             'gasPrice': w3.toWei('20', 'gwei'),
#             'nonce': w3.eth.getTransactionCount(account),
#         })

#         # Sign and send the transaction
#         private_key = os.getenv('PRIVATE_KEY')  # Fetch the private key from environment variables
#         signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
#         tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

#         # Wait for transaction receipt
#         tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#         contract_address = tx_receipt.contractAddress

#         # Output success message and save contract address to the model
#         self.stdout.write(self.style.SUCCESS(f'Contract deployed to {contract_address}'))
        
#         # Store contract address in database
#         LandTransaction.objects.update(smart_contract_address=contract_address)





















# from django.core.management.base import BaseCommand
# from web3 import Web3
# from transactions.models import LandTransaction
# from transactions.utils import load_contract_abi

# class Command(BaseCommand):
#     help = 'Deploys the LandTransaction smart contract'

#     def handle(self, *args, **options):
#         w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
#         account = w3.eth.accounts[0]

#         contract_abi = load_contract_abi()
#         contract_bytecode = "  0xC11D335a2C3977909eC2E8aBDfADE4AC84e4370C"

#         LandTransactionContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

#         oracle_address = '0x6Fb0D27e38fA6437a3BC2Bd10328310c8bC7F994'

#         tx_hash = LandTransactionContract.constructor(oracle_address).transact({'from': account})
#         tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#         contract_address = tx_receipt.contractAddress
#         self.stdout.write(self.style.SUCCESS(f'Contract deployed to {contract_address}'))

        
#         LandTransaction.objects.update(smart_contract_address=contract_address)