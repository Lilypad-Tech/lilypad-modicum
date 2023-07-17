import pycurl
import json
import logging
from io import BytesIO
from time import time, sleep
from threading import Thread, RLock
from . import config as cfg
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.middleware import construct_sign_and_send_raw_middleware
import os
import importlib
from hexbytes import HexBytes
from web3 import HTTPProvider, Web3
from web3.middleware import geth_poa_middleware, http_retry_request_middleware
import requests
from hexbytes import HexBytes

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

def GetEvents():
    abi = GetABI()
    events = {}
    for event in abi:
        if event["type"] == "event":
            args = []
            for arg in event["inputs"]:
                args.append((arg["name"], arg["type"]))
            events[event["name"]] = args
    return events

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

class NonceException(Exception):
    pass

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
        self.filter = self.w3.eth.filter({"fromBlock": self.w3.eth.block_number})
        self.generate_topics(GetEvents())
        
        # Polygon compatibility
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        # print(self.w3.is_connected())

        # Retry on nonce errors with linear backoff
        def retry_on_nonce_error(make_request, w3, retries=5):
            """
            Workaround:
            Traceback (most recent call last):
                File "/usr/lib/python3.10/threading.py", line 1016, in _bootstrap_inner
                    self.run()
                File "/usr/lib/python3.10/threading.py", line 953, in run
                    self._target(*self._args, **self._kwargs)
                File "/app/modicum/JobCreator.py", line 342, in platformListener
                    txHash = self.ethclient.contract.functions.acceptResult(resultId).transact({
                File "/usr/local/lib/python3.10/dist-packages/web3/contract/contract.py", line 479, in transact
                    return transact_with_contract_function(
                File "/usr/local/lib/python3.10/dist-packages/web3/contract/utils.py", line 172, in transact_with_contract_function
                    txn_hash = w3.eth.send_transaction(transact_transaction)
                File "/usr/local/lib/python3.10/dist-packages/web3/eth/eth.py", line 362, in send_transaction
                    return self._send_transaction(transaction)
                File "/usr/local/lib/python3.10/dist-packages/web3/module.py", line 68, in caller
                    result = w3.manager.request_blocking(
                File "/usr/local/lib/python3.10/dist-packages/web3/manager.py", line 232, in request_blocking
                    return self.formatted_response(
                File "/usr/local/lib/python3.10/dist-packages/web3/manager.py", line 205, in formatted_response
                    raise ValueError(response["error"])
                ValueError: {'code': -32000, 'message': 'nonce too low: next nonce 686, tx nonce 685'}
            """
            def middleware(method, params):
                for i in range(retries):
                    try:
                        rpc_response = make_request(method, params)
                        if "error" in rpc_response:
                            e = rpc_response["error"]
                            if e["code"] == -32000 and e["message"].startswith("nonce too low"):
                                raise NonceException(e["message"])
                        return rpc_response
                    except NonceException as e:
                        if i < retries - 1:
                            print(f"Retrying {method} in {i} seconds ({e})...")
                            time.sleep(i)
                            continue
                        else:
                            raise
                return None
            return middleware
        self.w3.middleware_onion.inject(retry_on_nonce_error, layer=0)

        # Retry on transient connection errors
        self.w3.middleware_onion.inject(http_retry_request_middleware, layer=0)

        self.addresses = []

        if os.environ.get('DEBUG') is not None:
            self.addresses = self.w3.eth.accounts

        pk = os.environ.get('PRIVATE_KEY')
        if pk is not None:
            acct = self.w3.eth.account.from_key(pk)
            self.addresses.append(acct.address)

            # Add acct as auto-signer:
            self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
        else:
            if os.environ.get('DEBUG') is None:
                raise Exception("No private key found in environment variable PRIVATE_KEY")

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
        # print(f"===> Web3EthereumClient command({method}, {self.summarize(params)}")
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
                # print(f"!!! --> get tx receipt --> {tx}")
                return self.w3.eth.get_transaction_receipt(tx)
            if method == "eth_blockNumber":
                return self.w3.eth.block_number
        except Exception as e:
            # print(f"exception calling command(): {e}, sleeping 1s and retrying, try {try_}...")
            sleep(1)
            return self.command(method, params, try_+1)
        raise Exception(f"Unexpected method {method}")

    @staticmethod
    def is_enum_defined(name):
        try:
            module = importlib.import_module('..Enums',__name__)
            getattr(module, name)
            return True
        except AttributeError:
            return False

    @staticmethod
    def get_enum_by_classname(name):
        module = importlib.import_module('..Enums',__name__)
        return getattr(module, name)

    def generate_topics(self, events):
        self.topics = {}
        for event in events:
            name = event
            topic = {'name': name}
            params = []
            for param in events[event]:
                ptype = param[1]
                pname = param[0]
                params.append((ptype, pname))
            topic['params'] = params

            # This part, converts enums to uint8 for checking signature hash.
            params = params.copy()
            for i in range(0, len(params)):
                if EthereumClient.is_enum_defined(params[i][0]):
                    params[i] = ('uint8', params[i][1])

            signature = "{}({})".format(name, ",".join([ptype for (ptype, pname) in params]))
            keccak256 = self.keccak256(signature)
            if not (keccak256.startswith("0x") and len(keccak256) == 66):
                raise Exception("Incorrect hash {} computed for signature {}!".format(keccak256, signature))
            self.topics[keccak256] = topic
        return self.topics

    def poll_events(self):
        log = self.filter.get_new_entries()
        events = []
        for item in log:
            if not isinstance(item, dict) and not isinstance(item, AttributeDict):
                self.logger.info(f"🟠🟠🟠🟠[poll_events] Skipping processing {item} since it is not a dict")
                continue
            if self.contract_address == item['address']:
                if maybe_hex(item['topics'][0]) in self.topics:
                    topic = self.topics[maybe_hex(item['topics'][0])]
                    event_name = topic['name']
                    zs = [x for x in self.abi if x["type"] == "event" and x["name"] == event_name]
                    if len(zs) != 1:
                        raise Exception('oh no the universe exploded')
                    event_abi = zs[0]
                    from web3 import _utils
                    raw_event = dict(_utils.events.get_event_data(self.w3.codec, event_abi, item))
                    raw_event["params"] = raw_event["args"]
                    raw_event["name"] = event_name
                    del raw_event["args"]
                    events.append(raw_event)
                else:
                  self.logger.info(f"🟠🟠🟠🟠[poll_events] Skipping processing {item} since the topic is not known {maybe_hex(item['topics'][0])}")

        return events

def maybe_hex(x):
    if isinstance(x, HexBytes):
        return x.hex()
    else:
        return x