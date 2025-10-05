import json
import os
from web3 import Web3

def load_contract_abi():
    """Load contract ABI from file"""
    contract_dir = os.path.dirname(__file__)
    abi_path = os.path.join(contract_dir, 'contract_abi.json')
    with open(abi_path, 'r') as file:
        return json.load(file)


def get_contract_instance(web3, contract_address):
    """Get contract instance at given address"""
    abi = load_contract_abi()
    return web3.eth.contract(address=contract_address, abi=abi)


def check_is_paid(web3, contract_address):
    """
    Check if payment has been made to the contract.

    Args:
        web3: Web3 instance
        contract_address: Address of the PaymentContract

    Returns:
        bool: True if paid, False otherwise
    """
    contract = get_contract_instance(web3, contract_address)
    return contract.functions.isPaid().call()


def assign_courier_tx(web3, contract_address, courier_address, owner_private_key):
    """
    Assign a courier to the order by calling contract's assignCourier function.

    Args:
        web3: Web3 instance
        contract_address: Address of the PaymentContract
        courier_address: Ethereum address of the courier
        owner_private_key: Private key of the owner

    Returns:
        tx_receipt: Transaction receipt
    """
    contract = get_contract_instance(web3, contract_address)
    owner_account = web3.eth.account.from_key(owner_private_key)
    owner_address = owner_account.address

    # Build transaction
    transaction = contract.functions.assignCourier(courier_address).build_transaction({
        'from': owner_address,
        'nonce': web3.eth.get_transaction_count(owner_address),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    # Sign and send
    signed_tx = web3.eth.account.sign_transaction(transaction, owner_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt


def confirm_delivery_tx(web3, contract_address, owner_private_key):
    """
    Confirm delivery and trigger payment distribution (80% owner, 20% courier).

    Args:
        web3: Web3 instance
        contract_address: Address of the PaymentContract
        owner_private_key: Private key of the owner

    Returns:
        tx_receipt: Transaction receipt
    """
    contract = get_contract_instance(web3, contract_address)
    owner_account = web3.eth.account.from_key(owner_private_key)
    owner_address = owner_account.address

    # Build transaction
    transaction = contract.functions.confirmDelivery().build_transaction({
        'from': owner_address,
        'nonce': web3.eth.get_transaction_count(owner_address),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    # Sign and send
    signed_tx = web3.eth.account.sign_transaction(transaction, owner_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt


def build_pay_transaction(web3, contract_address, customer_address, amount_wei):
    """
    Build (but don't send) a transaction for customer to pay the contract.
    This is used for /pay endpoint to generate an invoice.

    Args:
        web3: Web3 instance
        contract_address: Address of the PaymentContract
        customer_address: Ethereum address of the customer
        amount_wei: Payment amount in wei

    Returns:
        dict: Transaction object ready to be signed and sent by customer
    """
    contract = get_contract_instance(web3, contract_address)

    # Build transaction
    transaction = contract.functions.pay().build_transaction({
        'from': customer_address,
        'value': amount_wei,
        'nonce': web3.eth.get_transaction_count(customer_address),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    return transaction
