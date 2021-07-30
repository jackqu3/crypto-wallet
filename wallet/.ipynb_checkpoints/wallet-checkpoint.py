# Import dependencies
import subprocess
import json
import os
from dotenv import load_dotenv
from pprint import pprint

# Load and set environment variables
load_dotenv()
mnemonic = os.getenv("mnemonic")


# Import constants.py and necessary functions from bit and web3
from constants import *
from bit import Key, PrivateKey, PrivateKeyTestnet
from bit.network import NetworkAPI
from bit import *
from web3 import Web3, middleware, Account
from web3.gas_strategies.time_based import medium_gas_price_strategy
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1.8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Create a function called `derive_wallets`
def derive_wallets(coin, depth=3, mnemonic=mnemonic):
    command = f'./derive -g --mnemonic="{mnemonic}" --coin={coin} --numderive={depth} --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    return json.loads(output)

# Create a dictionary object called coins to store the output from `derive_wallets`.
coins = {
    ETH: derive_wallets(coin=ETH),
    BTCTEST: derive_wallets(coin=BTCTEST)
}
pprint(coins)

eth_private_key = coins["eth"][0]['privkey']
btctest_private_key = coins["btc-test"][0]['privkey']

# Create a function called `priv_key_to_account` that converts privkey strings to account objects.
def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    if coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)

eth_account = priv_key_to_account(ETH,eth_private_key)
btctest_account = priv_key_to_account(BTCTEST,btctest_private_key)

# Create a function called `create_tx` that creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, recipient, amount):
    if coin == ETH:
    # converts ETH to wei
        value = w3.toWei(amount, "ether") 
        gasEstimate = w3.eth.estimateGas({ "to": recipient, "from": account.address, "value": amount })
        return {
            "from": account.address,
            "to": recipient,
            "value": amount,
            "gasPrice": w3.eth.generateGasPrice(),
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address),
            "chainId": w3.net.chainId
        }
    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(recipient, amount, BTC)])

# Create a function called `send_tx` that calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, recipient, amount):
    if coin == ETH:
        raw_tx = create_tx(coin, account, recipient, amount)
        signed = account.signTransaction(raw_tx)
        result = w3.eth.sendRawTransaction(signed.rawTransaction)
        print(result.hex())
        return result.hex()

    if coin == BTCTEST:
        raw_tx = create_tx(coin, account, recipient, amount)
        signed = account.sign_transaction(raw_tx)
        return NetworkAPI.broadcast_tx_testnet(signed)

