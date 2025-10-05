import json
import os
from solcx import compile_source, install_solc

# Install solc compiler version 0.8.0
install_solc('0.8.0')

# Read contract source
contract_path = os.path.join(os.path.dirname(__file__), 'PaymentContract.sol')
with open(contract_path, 'r') as file:
    contract_source = file.read()

# Compile contract
compiled_sol = compile_source(
    contract_source,
    output_values=['abi', 'bin'],
    solc_version='0.8.0'
)

# Extract contract interface
contract_id, contract_interface = compiled_sol.popitem()

# Save ABI
abi_path = os.path.join(os.path.dirname(__file__), 'contract_abi.json')
with open(abi_path, 'w') as file:
    json.dump(contract_interface['abi'], file, indent=2)

# Save bytecode
bytecode_path = os.path.join(os.path.dirname(__file__), 'contract_bytecode.txt')
with open(bytecode_path, 'w') as file:
    file.write(contract_interface['bin'])

print("Contract compiled successfully!")
print(f"ABI saved to: {abi_path}")
print(f"Bytecode saved to: {bytecode_path}")
