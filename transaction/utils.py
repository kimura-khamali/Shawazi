# import json
# from django.conf import settings

# def load_contract_abi():
#     with open(settings.LAND_TRANSACTION_ABI_PATH, 'r') as abi_file:
#         return json.load(abi_file)
    
import json

def load_contract_abi(path):
    with open(path, 'r') as abi_file:
        return json.load(abi_file)

def load_contract_bytecode(path):
    with open(path, 'r') as bytecode_file:
        return bytecode_file.read().strip()

