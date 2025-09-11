import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

root_path = os.path.abspath(__file__)
root_path = '/'.join(root_path.split('/')[:-2])
sys.path.append(root_path)

from apexomni.http_private_sign import HttpPrivateSign  # Change to HttpPrivateSign for compatibility with eth methods
from apexomni.constants import APEX_OMNI_HTTP_TEST, NETWORKID_TEST, NETWORKID_OMNI_TEST_BNB

print("Hello, apexomni")

# Load keys from environment variables
priKey = os.getenv('ETH_PRIVATE_KEY')
seeds = os.getenv('ZK_SEEDS', '')
l2Key = os.getenv('ZK_L2_KEY', '')
key = os.getenv('API_KEY', '')
secret = os.getenv('API_SECRET', '')
passphrase = os.getenv('API_PASSPHRASE', '')

# Validate required environment variables
if not priKey:
    raise ValueError("ETH_PRIVATE_KEY environment variable is required")

print("Environment variables loaded successfully")

# Initialize with HttpPrivateSign
client = HttpPrivateSign(APEX_OMNI_HTTP_TEST, network_id=NETWORKID_TEST, eth_private_key=priKey,
                         zk_seeds=seeds,
                         zk_l2Key=l2Key,
                         api_key_credentials={'key': key, 'secret': secret, 'passphrase': passphrase})
configs = client.configs_v3()

# Poll for account
account = None
max_attempts = 20
attempt = 0
print("Fetching account...")
while account is None and attempt < max_attempts:
    account = client.get_account_v3()
    if account is None:
        print(f"...still waiting (attempt {attempt + 1}/{max_attempts})")
        time.sleep(6)
    attempt += 1

if account is None:
    raise ValueError(f"Failed to fetch account after {max_attempts} attempts. Ensure registration is complete and keys are valid.")

client.account = account
print("Account fetched:", account)

# Use 'id' from account
position_id = account.get('id')

# Approve if needed (uncomment if not already approved)
# approve_tx_hash = client.eth.set_token_max_allowance(client.eth.get_exchange_contract().address)
# print('Waiting for allowance...')
# client.eth.wait_for_tx(approve_tx_hash)
# print('...done.')

# Deposit
deposit_tx_hash = client.eth.deposit_to_exchange(
    position_id,
    0.1,  # Adjust amount
)
print('Waiting for deposit...')
client.eth.wait_for_tx(deposit_tx_hash)
print('...done.')

print("Deposit complete. Check your account balance.")