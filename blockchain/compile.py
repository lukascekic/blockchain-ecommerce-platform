import json
import os
from solcx import compile_source, install_solc

install_solc('0.8.0')

contract_file = os.path.join(os.path.dirname(__file__), 'PaymentContract.sol')
with open(contract_file, 'r') as f:
    source_code = f.read()

compiled = compile_source(
    source_code,
    output_values=['abi', 'bin'],
    solc_version='0.8.0'
)

contract_id, interface = compiled.popitem()

abi_file = os.path.join(os.path.dirname(__file__), 'contract_abi.json')
with open(abi_file, 'w') as f:
    json.dump(interface['abi'], f, indent=2)

bytecode_file = os.path.join(os.path.dirname(__file__), 'contract_bytecode.txt')
with open(bytecode_file, 'w') as f:
    f.write(interface['bin'])

print("Contract compiled successfully!")
print("ABI saved to: %s" % abi_file)
print("Bytecode saved to: %s" % bytecode_file)
