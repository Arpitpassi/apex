<codebase>
<project_structure>
.
├── .gitignore
├── deposit.py
└── pyproject.toml

0 directories, 3 files
</project_structure>

<file src=".gitignore">
.venv
.env

</file>

<file src="deposit.py">
import os
import sys
import time
from dotenv import load_dotenv

from apexomni.helpers.util import wait_for_condition
from apexomni.starkex.helpers import nonce_from_client_id

# Load environment variables from .env file
load_dotenv()

root_path = os.path.abspath(__file__)
root_path = '/'.join(root_path.split('/')[:-2])
sys.path.append(root_path)

from apexomni.http_private import HttpPrivate
from apexomni.constants import APEX_HTTP_TEST, NETWORKID_TEST, APEX_HTTP_MAIN, NETWORKID_MAIN

print("Hello, apexomni")

# Load credentials from environment variables
priKey = os.getenv('ETH_PRIVATE_KEY')

key = os.getenv('APEX_API_KEY')
secret = os.getenv('APEX_SECRET')
passphrase = os.getenv('APEX_PASSPHRASE')

public_key = os.getenv('STARK_PUBLIC_KEY')
public_key_y_coordinate = os.getenv('STARK_PUBLIC_KEY_Y_COORDINATE')
private_key = os.getenv('STARK_PRIVATE_KEY')

# Determine network configuration based on IS_TESTNET env variable
is_testnet = os.getenv('IS_TESTNET', 'false').lower() == 'true'
if is_testnet:
    http_endpoint = APEX_HTTP_TEST
    network_id = NETWORKID_TEST
else:
    http_endpoint = APEX_HTTP_MAIN
    network_id = NETWORKID_MAIN

client = HttpPrivate(http_endpoint, network_id=network_id, eth_private_key=priKey,
                     stark_public_key=public_key,
                     stark_private_key=private_key,
                     stark_public_key_y_coordinate=public_key_y_coordinate,
                     api_key_credentials={'key': key, 'secret': secret, 'passphrase': passphrase})
configs = client.configs()

account = client.get_account()

# If you have not approve usdc on eth, please approve first
# Set allowance on the Starkware perpetual contract, for the deposit.
#approve_tx_hash = client.eth.set_token_max_allowance(
#    client.eth.get_exchange_contract().address,
#)
print('Waiting for allowance...')
# Don't worry if you encounter a timeout request while waiting. Execution on the chain takes a certain time
#client.eth.wait_for_tx(approve_tx_hash)
print('...done.')

# Send an on-chain deposit.
deposit_tx_hash = client.eth.deposit_to_exchange(
    client.account['positionId'],
    0.1,
)
print('Waiting for deposit...')
# Don't worry if you encounter a timeout request while waiting. Execution on the chain takes a certain time

client.eth.wait_for_tx(deposit_tx_hash)
print('...done.')
</file>

<file src="pyproject.toml">
[project]
name = "my-project"
version = "0.1.0"
dependencies = [
    "apexomni",
    "python-dotenv>=1.0.0",
    "requests",
    "web3",
    "ecdsa",
    "mpmath",
    "sympy"
]

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
</file>

</codebase>
