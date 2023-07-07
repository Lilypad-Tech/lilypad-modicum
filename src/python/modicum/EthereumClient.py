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

        # Polygon compatibility
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        print(self.w3.is_connected())

        self.addresses = []
        for i in range(5):
            pk = os.environ.get(f'PRIVATE_KEY_{i}')
            if i == 0 and pk is None:
                pk = os.environ.get('PRIVATE_KEY')
            if pk is not None:
                acct = self.w3.eth.account.from_key(pk)
                self.addresses.append(acct.address)

                print(f"--> Loaded private key for {acct} from env PRIVATE_KEY_{i}")
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

    def transaction(self, from_address, data, value, to_address, try_=0):
        
        # self._i += 1
        # # pickle args into self._random_folder + f"/{self._i}.pkl"
        # print(f"--> transaction: {self._random_folder}/{self._i}.pkl")
        # with open(f"{self._random_folder}/{str(self._i).zfill(6)}.pkl", "wb") as f:
        #     import pickle
        #     pickle.dump((from_address, data, value, to_address), f)

        print(f"===> Web3EthereumClient transaction(from={from_address}, data={str(data)[:100]}, to={to_address}, try={try_})")
        if try_ > 30:
            raise Exception(f"Too many tries calling transaction()")
        try:
            return str(self.w3.eth.send_transaction({
                "gasPrice": self.w3.eth.gas_price,
                "from": from_address,
                "to": to_address,
                "data": data,
                "value": value,
            }).hex())
        except Exception as e:
            print(f"exception calling transaction(): {e}, sleeping 1s and retrying, try {try_}...")
            sleep(1)
            return self.transaction(from_address, data, value, to_address, try_+1)

    def accounts(self):
        if os.environ.get("PRIVATE_KEY_0") is not None:
            print(f"--> addresses = {self.addresses}")
            return self.addresses
        return self.w3.eth.accounts

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

    def new_filter(self):
        # TODO: now we have self.contract, should we use it like
        #     event_filter = mycontract.events.myEvent.create_filter(fromBlock='latest', argument_filters={'arg1':10})
        # ?
        self._filter = self.w3.eth.filter({"fromBlock": self.w3.eth.block_number})
        self.filter_id = self._filter.filter_id
        return self.filter_id

    def get_filter_changes(self, filter_id):
        # XXX filter_id is not used, remove it from all callers and then from here
        ch = self._filter.get_new_entries()
        # print(f"--> in get_filter_changes({filter_id}), got {ch}")
        return ch


CHECK_INTERVAL = 1  # check for receipts every second
PENDING_TIMEOUT = 120  # if a transaction has been pending for more than 120 seconds, submit it again
CLIENT_TIMEOUT = 600  # if a transaction has been stuck for more than 600 seconds, restart the client



class OldEthereumClient:
# class EthereumClient:
    def __init__(self, ip, port):
        self.logger = logging.getLogger("EthereumClient")
        self.logger.setLevel(logging.INFO)

        # ch = logging.StreamHandler()platformListener
        # formatter = logging.Formatter("---%(name)s---: \n%(message)s\n\r")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.ip = ip
        self.port = port
        self.waiting = []  # transactions which have not been submitted
        self.pending = []  # transactions which have been submitted but not yet mined
        self.lock = RLock()
        self.quit = False
        self.thread = Thread(target=self.__run)
        self.thread.start()

        # print("self.quit %s" %self.quit)

    def __run(self):
        while not self.quit:
            sleep(CHECK_INTERVAL)  # wait one second
            current_time = time()
            with self.lock:
                for trans in self.pending + self.waiting:
                    if current_time > trans[
                        'request_time'] + CLIENT_TIMEOUT:  # transaction has been stuck for a long time
                        self.__restart_client()
                for trans in list(self.pending):  # iterate over a copy so that we can remove items
                    receipt = self.command("eth_getTransactionReceipt", params=[trans['hash']])
                    if receipt is not None:  # transaction receipt is available
                        self.pending.remove(trans)
                        self.logger.debug("Transaction {} has been mined.".format(trans['data']))

                        self.logger.info(receipt)

                        if receipt['gasUsed'] == cfg.TRANSACTION_GAS:
                            self.logger.warning("WARNING: Transaction Failed")
                            self.logger.warning(receipt)
                    elif current_time > trans['submission_time'] + PENDING_TIMEOUT:  # timeout for pending transaction
                        self.pending.remove(trans)
                        self.logger.debug("Pending transaction {} has timed out, resubmitting...".format(trans['data']))
                        self.__submit_trans(trans)
                    # otherwise, wait more for this transaction
                for trans in list(self.waiting):  # iterate over a copy so that we can remove items
                    self.waiting.remove(trans)
                    self.__submit_trans(trans)  # resubmit

    def __restart_client(self):
        self.logger.debug("Restarting the client...")
        # TODO: writeme
        # TODO: handle filter re-creation?

    def exit(self):
        self.logger.info("exit %s thread" % __name__)
        self.quit = True
        self.thread.join()

    def __submit_trans(self, trans):
        try:
            params = [{
                'from': trans['from'],
                'data': trans['data'],
                'to': trans['to'],
                'value': trans['value'],
                'gas': hex(cfg.TRANSACTION_GAS)
            }]

            self.logger.info("Estimate gas")
            gasEstimate = self.command("eth_estimateGas", params=params)
            self.logger.info("Estimate of gas requirement to submit transaction: %s" %gasEstimate)

            trans_hash = self.command("eth_sendTransaction", params=params)

            if trans_hash.startswith(
                    "0x"):  # this looks like a transaction hash (this check could be more thorough of course...)
                trans['hash'] = trans_hash
                trans['submission_time'] = time()
                self.logger.debug("Transaction {} has been submitted...".format(trans_hash))
                self.pending.append(trans)  # keep track of pending transactions
                # return 0# success, nothing else to do
                return trans_hash
        except BaseException as e:
            print("ERROR")
            self.logger.error(str(e))
        # something went wrong
        self.logger.warning("Failed to submit transaction {}...".format(trans_hash))
        self.waiting.append(trans)  # keep track of transaction which have not been submitted
        return 1

    def transaction(self, from_address, data, value, to_address):
        trans = {
            'request_time': time(),
            'from': from_address,
            'to': to_address,
            'data': data,
            'value': value
        }
        with self.lock:
            exitcode = self.__submit_trans(trans)
        return exitcode


    def accounts(self):
        return self.command("eth_accounts")

    def keccak256(self, string):
        return self.command("web3_sha3", params=["0x" + bytes(string, 'ascii').hex()])

    def new_filter(self):
        self.filter_id = self.command("eth_newFilter", params=[{"fromBlock": "0x1"}])
        self.logger.debug("Created filter (ID = {}).".format(self.filter_id))
        return self.filter_id

    def get_filter_changes(self, filter_id):
        block = self.command("eth_blockNumber")
        
        try:
            log = self.command("eth_getFilterChanges", params=[self.filter_id])
            if len(log) > 0:
                self.logger.debug("Log: {} items (block number: {})".format(len(log), block))
            return log
        except Exception as inst:
            '''Added this try/except becuase occassionally would get 
            error: "filter not found", apparently geth throws them away after some time. 
            The web3.py middleware (https://github.com/ethereum/web3.py/blob/master/docs/middleware.rst#locally-managed-log-and-block-filters) handles it. 
            The problem was discussed here (https://github.com/ethereum/web3.py/pull/732). 
            I'm not sure if what is here will work'''

            self.logger.info("EXCEPTION MESSAGE: %s" %inst)
            if inst.args[1]['error']['message'] == 'filter not found':
                self.filter_id = self.new_filter()
                log = self.get_filter_changes(self.filter_id)
                self.logger.info("LOG: %s" %log)
                return log

    def command(self, method, params=[], id=1, jsonrpc="2.0", verbose=False):
        """ Send command (method with given parameters) to geth client over RPC using PycURL """
        # IP and port for connection
        ip_port = str(self.ip) + ":" + str(self.port)
        # buffer to capture output
        buffer = BytesIO()
        # start building curl command to process
        c = pycurl.Curl()
        c.setopt(pycurl.URL, ip_port+"/rpc/v1")
        c.setopt(pycurl.HTTPHEADER, ['Content-type:application/json'])
        c.setopt(pycurl.WRITEFUNCTION, buffer.write)
        data2 = {"jsonrpc": str(jsonrpc), "method": str(method), "params": params, "id": str(id)}
        data = json.dumps(data2)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, data)

        if verbose:
            c.setopt(pycurl.VERBOSE, 1)
        # perform pycurl
        try:
            c.perform()
        except pycurl.error as e:
            # print("THE ERROR: %s" %e)
            return "RPC failed, THE ERROR: %s" % e
            # print(e)
            # print(e[1])

        # check response code (HTTP codes)
        # if (c.getinfo(pycurl.RESPONSE_CODE) != 200):
        #   raise Exception('rpc_communication_error', "response code is {} insted of 200".format(c.getinfo(pycurl.RESPONSE_CODE)))
        # close pycurl object
        c.close()

        # decode result
        results = str(buffer.getvalue().decode('iso-8859-1'))
        if verbose:
            print(results)

        # convert result to json object for parsing
        data = json.loads(results)
        # return appropriate result
        if 'result' in data.keys():
            return data["result"]
        else:
            if 'error' in data.keys():
                raise Exception('rpc_communication_error', data)
            else:
                raise Exception('rpc_communication_error',
                                "unknown error: possibly method/parameter(s) were wrong and/or networking issue.")
