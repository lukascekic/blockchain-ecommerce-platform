import json
import os
from web3 import Web3

def load_contract_abi():
    dir_path = os.path.dirname(__file__)
    abi_file = os.path.join(dir_path, 'contract_abi.json')
    with open(abi_file, 'r') as f:
        return json.load(f)


def get_contract_instance(web3, contract_address):
    contract_abi = load_contract_abi()
    return web3.eth.contract(address=contract_address, abi=contract_abi)


def check_is_paid(web3, contract_address):
    contract_inst = get_contract_instance(web3, contract_address)
    return contract_inst.functions.isPaid().call()


def assign_courier_tx(web3, contract_address, courier_address, owner_private_key):
    contract_inst = get_contract_instance(web3, contract_address)
    owner_acc = web3.eth.account.from_key(owner_private_key)
    owner_addr = owner_acc.address

    tx = contract_inst.functions.assignCourier(courier_address).build_transaction({
        'from': owner_addr,
        'nonce': web3.eth.get_transaction_count(owner_addr),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    signed = web3.eth.account.sign_transaction(tx, owner_private_key)
    hash_val = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(hash_val)

    return receipt


def confirm_delivery_tx(web3, contract_address, owner_private_key):
    contract_inst = get_contract_instance(web3, contract_address)
    owner_acc = web3.eth.account.from_key(owner_private_key)
    owner_addr = owner_acc.address

    tx = contract_inst.functions.confirmDelivery().build_transaction({
        'from': owner_addr,
        'nonce': web3.eth.get_transaction_count(owner_addr),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    signed = web3.eth.account.sign_transaction(tx, owner_private_key)
    hash_val = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(hash_val)

    return receipt


def build_pay_transaction(web3, contract_address, customer_address, amount_wei):
    contract_inst = get_contract_instance(web3, contract_address)

    tx = contract_inst.functions.pay().build_transaction({
        'from': customer_address,
        'value': amount_wei,
        'nonce': web3.eth.get_transaction_count(customer_address),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    return tx
