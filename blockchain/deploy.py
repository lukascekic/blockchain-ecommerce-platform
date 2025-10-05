import json
import os
from web3 import Web3

# Load contract ABI and bytecode
def load_contract_data():
    """Load compiled contract ABI and bytecode"""
    contract_dir = os.path.dirname(__file__)

    abi_path = os.path.join(contract_dir, 'contract_abi.json')
    with open(abi_path, 'r') as file:
        abi = json.load(file)

    bytecode_path = os.path.join(contract_dir, 'contract_bytecode.txt')
    with open(bytecode_path, 'r') as file:
        bytecode = file.read()

    return abi, bytecode


def deploy_payment_contract(web3, owner_private_key, customer_address, amount_wei):
    """
    Deploy a new PaymentContract to the blockchain.

    Args:
        web3: Web3 instance connected to Ganache
        owner_private_key: Private key of the owner (deployer)
        customer_address: Ethereum address of the customer
        amount_wei: Payment amount in wei

    Returns:
        contract_address: Address of the deployed contract
    """
    # Load contract data
    abi, bytecode = load_contract_data()

    # Get owner account from private key
    owner_account = web3.eth.account.from_key(owner_private_key)
    owner_address = owner_account.address

    # Create contract instance
    PaymentContract = web3.eth.contract(abi=abi, bytecode=bytecode)

    # Build constructor transaction
    constructor_tx = PaymentContract.constructor(customer_address, amount_wei)

    # Estimate gas
    gas_estimate = constructor_tx.estimate_gas({'from': owner_address})

    # Build transaction
    transaction = constructor_tx.build_transaction({
        'from': owner_address,
        'nonce': web3.eth.get_transaction_count(owner_address),
        'gas': gas_estimate,
        'gasPrice': web3.eth.gas_price
    })

    # Sign transaction
    signed_tx = web3.eth.account.sign_transaction(transaction, owner_private_key)

    # Send transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    contract_address = tx_receipt.contractAddress

    return contract_address
