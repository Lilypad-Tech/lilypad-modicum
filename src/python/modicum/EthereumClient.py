import pycurl
import json
import logging
from io import BytesIO
from time import time, sleep
from threading import Thread, RLock
from . import config as cfg
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware
import os

from hexbytes import HexBytes
from web3 import HTTPProvider, Web3
from web3.middleware import geth_poa_middleware
import requests

def GetABIFile():
    contractABIFile = os.getenv("CONTRACT_ABI_FILE", "/Modicum.json")
    try:
        f = open(contractABIFile, "r")
        f.close()
    except FileNotFoundError:
        raise FileNotFoundError
    # open the JSON file and parse it
    with open(contractABIFile, "r") as f:
        contractABI = json.load(f)
    return contractABI

def GetABI():
    file = GetABIFile()
    return file["abi"]

def GetBytecode():
    file = GetABIFile()
    return file["bytecode"]


class CustomHTTPProvider(HTTPProvider):
    def __init__(self, endpoint_uri, request_kwargs=None):
        super().__init__(endpoint_uri, request_kwargs)
        # if 'headers' not in self._request_kwargs:
        #     self._request_kwargs['headers'] = {}
        rpcToken = os.getenv("RPC_TOKEN")
        if rpcToken != None:
            self._request_kwargs['headers']['Authorization'] = f'Bearer {rpcToken}'

class EthereumClient:
    def __init__(self, ip, port, protocol=None):
        self.logger = logging.getLogger("EthereumClient")
        self.logger.setLevel(logging.INFO)
        self.ip = ip
        self.port = port
        if protocol is None:
            # do some guessing
            if port == "443":
                protocol = "https"
            else:
                protocol = "http"

        if os.getenv("RPC_URL") is not None:
            self.w3 = Web3(CustomHTTPProvider(os.getenv("RPC_URL")))
        else:
            self.w3 = Web3(CustomHTTPProvider(f'{protocol}://{self.ip}:{self.port}'))

        self.abi = GetABI()
        self.bytecode = GetBytecode()
        self.contract_address = os.environ.get("CONTRACT_ADDRESS")
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi, bytecode=self.bytecode)
        # self.filter = self.w3.eth.filter({"fromBlock": self.w3.eth.block_number})
        self.filter = self.w3.eth.filter('latest')

        # Polygon compatibility
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        print(self.w3.is_connected())

        self.addresses = self.w3.eth.accounts
        for i in range(5):
            pk = os.environ.get(f'PRIVATE_KEY_{i}')
            if i == 0 and pk is None:
                pk = os.environ.get('PRIVATE_KEY')
            if pk is not None:
                acct = self.w3.eth.account.from_key(pk)
                self.addresses[i] = acct.address

                print(f"--> Loaded private key for {acct.address} from env PRIVATE_KEY_{i}")
                # Add acct as auto-signer:
                self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
                # Transactions from `acct` will then be signed, under the hood, in
                # the middleware.
        
        self._filter = None
        self.filter_id = None
        self._i = 0
        # Generate random string
        self._random_string = "debug_" + os.urandom(32).hex()
        # Create random folder
        self._random_folder = os.path.join(os.getcwd(), self._random_string)
        os.mkdir(self._random_folder)

    def exit(self):
        return

    def keccak256(self, string):
        r = self.w3.solidity_keccak(['string'], [string])
        return str(r.hex())
    
    def summarize(self, params):
        """
        Summarize params for debug printing
        """
        try:
            # Intentionally disregard any exceptions
            if len(params) == 1 and "data" in params[0]:
                s = dict(params[0])
                s["data"] = s["data"][:50]
                return str(s)
        except Exception as e:
            pass
        return str(params)[:100]

    def command(self, method, params, verbose=False, try_=0):

        # # Normalize strings starting with 0x, HexBytes instances and raw bytes
        # # all down to raw bytes
        # if len(params) == 1:
        #     if isinstance(params[0], bytes):
        #         params[0] = HexBytes(params[0])
        #     # if isinstance(params[0], HexBytes):
        #     #     params[0] = bytes(params[0])
        #     if isinstance(params[0], str):
        #         params[0] = HexBytes(params[0])

        self._i += 1
        # pickle args into self._random_folder + f"/{self._i}.pkl"
        # print(f"--> transaction: {self._random_folder}/{self._i}.pkl")
        # with open(f"{self._random_folder}/{str(self._i).zfill(6)}.pkl", "wb") as f:
        #     import pickle
        #     pickle.dump(("command", method, params), f)

        if try_ > 30:
            raise Exception(f"Too many tries calling command()")
        print(f"===> Web3EthereumClient command({method}, {self.summarize(params)}")
        try:
            if method == "eth_estimateGas":
                tx = params[0]
                if "data" not in tx:
                    return 0
                return self.w3.eth.estimate_gas(tx)
            if method == "eth_sendTransaction":
                tx = params[0]
                if "gasPrice" not in tx:
                    tx["gasPrice"] = self.w3.eth.gas_price
                return self.w3.eth.send_transaction(tx)
            if method == "eth_getTransactionReceipt":
                tx = params[0]
                print(f"!!! --> get tx receipt --> {tx}")
                return self.w3.eth.get_transaction_receipt(tx)
            if method == "eth_blockNumber":
                return self.w3.eth.block_number
        except Exception as e:
            print(f"exception calling command(): {e}, sleeping 1s and retrying, try {try_}...")
            sleep(1)
            return self.command(method, params, try_+1)
        raise Exception(f"Unexpected method {method}")

    def poll_events(self):
        self.logger.info("🔴🔴🔴🔴🔴🔴🔴🔴 poll_events.")
        events = []
        for event in self.filter.get_new_entries():
            import pprint; pprint.pprint(event)

        # logs = self.filter.get_new_entries()
        # events = []
        # import pprint; pprint.pprint(logs)
        # for item in log:
        #     if not isinstance(item, dict) and not isinstance(item, AttributeDict):
        #         self.logger.info(f"[poll_events] Skipping processing {item} since it is not a dict")
        #         continue
        #     if self.address == item['address']:
        #         if maybe_hex(item['topics'][0]) in self.topics:
        #             topic = self.topics[maybe_hex(item['topics'][0])]
        #             event_name = topic['name']
        #             zs = [x for x in self.client.abi if x["type"] == "event" and x["name"] == event_name]
        #             if len(zs) != 1:
        #                 raise Exception('oh no the universe exploded')
        #             event_abi = zs[0]
        #             from web3 import _utils
        #             raw_event = dict(_utils.events.get_event_data(self.client.w3.codec, event_abi, item))
        #             raw_event["params"] = raw_event["args"]
        #             raw_event["name"] = event_name
        #             del raw_event["args"]
        #             events.append(raw_event)

        return events

