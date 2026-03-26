import os
import json
import logging
import traceback
import time
from dotenv import load_dotenv

from locust import User, task, tag, between, LoadTestShape, events
from web3 import Web3, HTTPProvider
from eth_account import Account

ENV_FILE = os.getenv("ENV_FILE")
if ENV_FILE is not None:
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()

RPC_URL = os.getenv("RPC_URL")
MNEMONIC = os.getenv("MNEMONIC")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
INPUTBOX_ADDRESS = os.getenv("INPUTBOX_ADDRESS")
APP_ADDRESS = os.getenv("APP_ADDRESS")

INPUTBOX_ABI_FILE = os.getenv("INPUTBOX_ABI_FILE") or 'InputBox.json'

MIN_WAIT = int(os.getenv("MIN_WAIT") or 2)
MAX_WAIT = int(os.getenv("MAX_WAIT") or 10)

MIN_BALANCE =                300_000_000_000_000
BALANCE_TO_TRANSFER =      3_000_000_000_000_000
MIN_FUND_WALLET_BALANCE =  5_000_000_000_000_000
TXETH_GAS = 21000

GAMEPLAY_PREFIX = os.getenv("GAMEPLAY_PREFIX") or 'gameplay'

LONG_GAMEPLAY_NAME = f"{GAMEPLAY_PREFIX}-long"
MEDIUM_GAMEPLAY_NAME = f"{GAMEPLAY_PREFIX}-medium"
SHORT_GAMEPLAY_NAME = f"{GAMEPLAY_PREFIX}-short"

TIMELIMIT = 1200

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

Account.enable_unaudited_hdwallet_features()

class W3Client:
    def __init__(self,account_index=0):
        if not RPC_URL or not MNEMONIC or not PRIVATE_KEY or not INPUTBOX_ADDRESS or not INPUTBOX_ABI_FILE or not APP_ADDRESS:
            raise Exception("Missing envs.")
        self.w3 = Web3(HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            raise Exception("web3 client not connected.")
        self.account = self.w3.eth.account.from_mnemonic(MNEMONIC, account_path=f"m/44'/60'/0'/0/{account_index}")
        # self.account = self.w3.eth.account.from_key(PRIVATE_KEY)
        abi = {}
        with open(INPUTBOX_ABI_FILE) as file:
            abi = json.load(file)
        self.contract = self.w3.eth.contract(address=INPUTBOX_ADDRESS, abi=abi)

    def fund(self,amount):
        fund_account = self.w3.eth.account.from_key(PRIVATE_KEY)
        fund_balance = self.w3.eth.get_balance(fund_account.address)
        LOGGER.info(f"  Funding {self.account.address} ({self.w3.eth.get_balance(self.account.address):_=}) from {fund_account.address} ({fund_balance:_=} wei)")

        if fund_balance < MIN_FUND_WALLET_BALANCE:
            # don't transfer anymore
            LOGGER.info(f"    Won't fund {self.account.address} from {fund_account.address}, ")
            return

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = latest_block.baseFeePerGas
        max_priority_fee_per_gas = self.w3.to_wei(1, 'gwei')
        max_fee_per_gas = (5 * base_fee_per_gas) + max_priority_fee_per_gas # Maximum amount you’re willing to pay

        # Define the transaction parameters
        tx = {
            'from': fund_account.address,
            'to': self.account.address,
            'value': amount,
            'nonce': self.w3.eth.get_transaction_count(fund_account.address),
            'gas': TXETH_GAS,
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'chainId': self.w3.eth.chain_id
        }

        # Sign the transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx, fund_account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status'] == 1:
            LOGGER.info(f"    Fund Transaction successful {self.account.address}. Block: {tx_receipt['blockNumber']}, Gas: {tx_receipt['gasUsed']:_=}, Gas Price: {tx_receipt['effectiveGasPrice']:_=} Fee: {(tx_receipt['gasUsed']*tx_receipt['effectiveGasPrice']):_=}")
            return True
        LOGGER.error(f"    Fund Transaction failed {self.account.address}")

    def refund(self):
        refund_account = self.w3.eth.account.from_key(PRIVATE_KEY)
        balance = self.w3.eth.get_balance(self.account.address)
        LOGGER.info(f"  Refunding try {refund_account.address} ({self.w3.eth.get_balance(refund_account.address):_=} wei) from {self.account.address} ({balance:_=} wei)")

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = latest_block.baseFeePerGas
        max_priority_fee_per_gas = self.w3.to_wei(1, 'gwei')
        max_fee_per_gas = (5 * base_fee_per_gas) + max_priority_fee_per_gas # Maximum amount you’re willing to pay

        if balance < 2*TXETH_GAS*max_fee_per_gas:
            # don't transfer anymore
            LOGGER.info(f"  Won't refund {refund_account.address} from {self.account.address}")
            return

        amount = balance - 2*TXETH_GAS*max_fee_per_gas
        LOGGER.info(f"  Refunding {refund_account.address} from {self.account.address} {amount:_} wei {max_fee_per_gas:_=} {TXETH_GAS:_=}")

        # Define the transaction parameters
        tx = {
            'from': self.account.address,
            'to': refund_account.address,
            'value': amount,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': TXETH_GAS,
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'chainId': self.w3.eth.chain_id
        }

        # Sign the transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status'] == 1:
            LOGGER.info(f"    Refund Transaction successful {self.account.address}. Block: {tx_receipt['blockNumber']}, Gas: {tx_receipt['gasUsed']}, Gas Price: {tx_receipt['effectiveGasPrice']} Fee: {tx_receipt['gasUsed']*tx_receipt['effectiveGasPrice']}")
            return True
        LOGGER.error(f"    Refund Transaction failed {self.account.address}")

    def send(self,payload):
        # # Set up sender account
        sender_balance = self.w3.eth.get_balance(self.account.address)
        if sender_balance < MIN_BALANCE:
            self.fund(BALANCE_TO_TRANSFER)
            time.sleep(between(MIN_WAIT, MAX_WAIT)(0))

        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = latest_block.baseFeePerGas
        max_priority_fee_per_gas = self.w3.to_wei(1, 'gwei')
        max_fee_per_gas = (5 * base_fee_per_gas) + max_priority_fee_per_gas # Maximum amount you’re willing to pay

        nonce = self.w3.eth.get_transaction_count(self.account.address)
        LOGGER.info(f"New Transaction {self.account.address}({nonce}) ")

        tx = self.contract.functions.addInput(APP_ADDRESS,payload).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'gas': 100000,  # Reasonable gas limit for simple operations
            # 'gasPrice': w3.eth.gas_price
        })
        LOGGER.info(f"    Transaction built {self.account.address}({nonce}), Gas Limit: {tx.get('gas')}, Gas Price: {tx.get('gasPrice')} wei, Max fee {tx.get('maxFeePerGas')}")

        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
        LOGGER.info(f"    Transaction signed {self.account.address}({nonce})")
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        LOGGER.info(f"    Transaction sent {self.account.address}({nonce}). Tx hash {tx_hash}. waiting for receipt")
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt['status'] == 1:
            LOGGER.info(f"    Transaction successful {self.account.address}({nonce}). Block: {tx_receipt['blockNumber']}, Gas: {tx_receipt['gasUsed']}, Gas Price: {tx_receipt['effectiveGasPrice']} Fee: {tx_receipt['gasUsed']*tx_receipt['effectiveGasPrice']}")
            return True
        LOGGER.error(f"    Transaction failed {self.account.address}({nonce}) {len(payload)=}")
        return False

class DAClient(W3Client):

    def __init__(self, request_event, account_index=0):
        super().__init__(account_index)
        self._request_event = request_event
        self.account_index = account_index

    def send_gameplay(self, gameplay_name):
        payload = '0x'
        with open(f"{gameplay_name}.outhash",'r') as file:
            payload += file.read()
        with open(f"{gameplay_name}.rivlog",'rb') as file:
            gameplay_bytes = file.read()
            payload += gameplay_bytes.hex()

        request_meta = {
            "request_type": "eth_tx",
            "request_method": gameplay_name,
            "name": f"{gameplay_name}_idx-{self.account_index}",
            "start_time": time.time(),
            "response_length": 0,  # calculating this for an xmlrpc.client response would be too hard
            "response": None,
            "context": {},  # see HttpUser if you actually want to implement contexts
            "exception": None,
        }
        start_perf_counter = time.perf_counter()
        try:
            LOGGER.info(f"Sending gameplay (sccount index {self.account_index}): {gameplay_name} ({len(payload)} bytes)")
            request_meta["response"] = self.send(payload)
        except Exception as e:
            LOGGER.error(f"Error: {e}")
            LOGGER.error(traceback.format_exc())
            request_meta["exception"] = e
        request_meta["response_time"] = (time.perf_counter() - start_perf_counter) * 1000
        self._request_event.fire(**request_meta)  # This is what makes the request actually get logged in Locust
        return request_meta["response"]


class W3User(User):
    n_users = 0
    abstract = True  # dont instantiate this as an actual user when running Locust
    clients_created = []
    def __init__(self, environment):
        super().__init__(environment)
        self.client = DAClient(environment.events.request, W3User.n_users)
        W3User.n_users += 1
        W3User.clients_created.append(self.client)

    def context(self):
        return {"client": self.client}

@events.test_stop.add_listener
def clients_refund(environment, **kwargs):
    for client in W3User.clients_created:

        time.sleep(between(MIN_WAIT, MAX_WAIT)(0))
        client.refund()


class GameplayUser(W3User):
    weight = 1 # in relation to other Users

    @tag('short')
    @task
    def send_short_gameplay(self):
        self.client.send_gameplay('gameplay-short')

    @tag('medium')
    @task
    def send_medium_gameplay(self):
        self.client.send_gameplay('gameplay-medium')

    @tag('long')
    @task
    def send_long_gameplay(self):
        self.client.send_gameplay('gameplay-long')

    wait_time = between(MIN_WAIT, MAX_WAIT)
    # def wait_time(self):
    #     self.last_wait_time += 1
    #     return self.last_wait_time

# class MyCustomShape(LoadTestShape):
#     use_common_options = True

#     def tick(self):
#         run_time = self.get_run_time()
#         timelimit = TIMELIMIT
#         if self.runner.environment.parsed_options.run_time is not None:
#             timelimit = self.runner.environment.parsed_options.run_time
#         if run_time < timelimit:
#             # User count rounded to nearest hundred, just like in previous example
#             user_count = round(self.runner.environment.parsed_options.spawn_rate*run_time,0) + 1
#             if self.runner.environment.parsed_options.users is not None:
#                 user_count = min(user_count,self.runner.environment.parsed_options.users)
#             return (user_count, self.runner.environment.parsed_options.spawn_rate)

#         return None

# Refund
"""
import locustfile

cs = []
n_users = 17
for i in range(n_users): cs.append(locustfile.W3Client(i))

for c in cs: c.refund()


"""
