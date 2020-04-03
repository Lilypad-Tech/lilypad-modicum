import sys
sys.path.append(".")

import os
print (os.getcwd())

from src.python.modicum.bytecode import BYTECODE

import hashlib
contractHash = hashlib.sha256(BYTECODE.encode()).hexdigest()


import json

contract = {}

with open ('src/python/modicum/helpers/contract.json','r') as f : 
    try:
        contract = json.load(f)
    except json.decoder.JSONDecodeError:
        print("json is empty")

with open('src/python/modicum/helpers/contract.json','w') as f : 
    try:
        if contract['hash'] != contractHash:
            contract['contractAddress'] = self.deploy_contract(BYTECODE,TRANSACTION_GAS,verbose)
            contract['hash'] = contractHash
        else:
            contract_address = contract['contractAddress']
        
    except KeyError:
        contract['hash'] = contractHash
        contract['contractAddress'] = 7

    print(contract)

    json.dump(contract,f)
