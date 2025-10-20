import json
import os
from web3 import Web3

def load_contract_data():
    dir_path = os.path.dirname(__file__)

    abi_file = os.path.join(dir_path, 'contract_abi.json')
    with open(abi_file, 'r') as f:
        contract_abi = json.load(f)

    bytecode_file = os.path.join(dir_path, 'contract_bytecode.txt')
    with open(bytecode_file, 'r') as f:
        contract_bytecode = f.read()

    return contract_abi, contract_bytecode


def deploy_payment_contract(web3, owner_private_key, customer_address, amount_wei):
    contract_abi, contract_bytecode = load_contract_data()

    owner_acc = web3.eth.account.from_key(owner_private_key)
    owner_addr = owner_acc.address

    contract = web3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

    constructor = contract.constructor(customer_address, amount_wei)

    gas_est = constructor.estimate_gas({'from': owner_addr})

    tx = constructor.build_transaction({
        'from': owner_addr,
        'nonce': web3.eth.get_transaction_count(owner_addr),
        'gas': gas_est,
        'gasPrice': web3.eth.gas_price
    })

    signed = web3.eth.account.sign_transaction(tx, owner_private_key)

    hash_tx = web3.eth.send_raw_transaction(signed.raw_transaction)

    receipt = web3.eth.wait_for_transaction_receipt(hash_tx)

    addr = receipt.contractAddress

    return addr
