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

# TODO: is it because the eth client is supposed to be polling?
# XXX: no, it seems like the JC never finishes registering...
# A-ha: cli.py:243 never hits JC.registered = true
# TODO: what to do next: try to port the threading code in the previous Ethereum
# client to the new one. I'm not entirely sure why we need it, but we probably
# do.

class EthereumClient:
# class NewEthereumClient:
    def __init__(self, ip, port, protocol='http'):
        self.ip = ip
        self.port = port

        self.w3 = Web3(Web3.HTTPProvider(f'{protocol}://{self.ip}:{self.port}'))
        print(self.w3.is_connected())

        for i in range(5):
            pk = os.environ.get(f'PRIVATE_KEY_{i}')
            if pk is not None:
                acct = self.w3.eth.account.from_key(pk)
                # Add acct as auto-signer:
                self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
                # Transactions from `acct` will then be signed, under the hood, in
                # the middleware.
        
        self._filter = None
        self.filter_id = None

    def exit(self):
        return

    def transaction(self, from_address, data, value, to_address):
        return str(self.w3.eth.send_transaction({
            "from": from_address,
            "to": to_address,
            "data": data,
            "value": value,
        }).hex())

    def accounts(self):
        return self.w3.eth.accounts

    def keccak256(self, string):
        r = self.w3.solidity_keccak(['string'], [string])
        return str(r.hex())
    
    def command(self, method, params, verbose=False):
        print(f"===> Web3EthereumClient command({method}, {str(params)[:100]})")
        if method == "eth_estimateGas":
            tx = params[0]
            if "data" not in tx:
                return 0
            return self.w3.eth.estimate_gas(tx)
        if method == "eth_sendTransaction":
            tx = params[0]
            return self.w3.eth.send_transaction(tx)
        if method == "eth_getTransactionReceipt":
            tx = params[0]
            import ipdb; ipdb.set_trace()
            return self.w3.eth.get_transaction_receipt(tx)
        raise Exception(f"Unexpected method {method}")

    def new_filter(self):
        self._filter = self.w3.eth.filter({"fromBlock": "0x1"})
        self.filter_id = self._filter.filter_id
        return self.filter_id

    def get_filter_changes(self, filter_id):
        # XXX filter_id is not used, remove it from all callers and then from here
        return self._filter.get_new_entries()


CHECK_INTERVAL = 1  # check for receipts every second
PENDING_TIMEOUT = 120  # if a transaction has been pending for more than 120 seconds, submit it again
CLIENT_TIMEOUT = 600  # if a transaction has been stuck for more than 600 seconds, restart the client



class OldEthereumClient:
# class EthereumClient:
    def __init__(self, ip, port):
        self.logger = logging.getLogger("EthereumClient")
        self.logger.setLevel(logging.INFO)

        # ch = logging.StreamHandler()
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
