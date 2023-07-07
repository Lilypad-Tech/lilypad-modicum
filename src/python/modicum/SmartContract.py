import os
import logging
import json
from threading import Thread
import requests
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

def GetABIFile():
    logger = logging.getLogger("GetABIFile")
    contractABIFile = os.getenv("CONTRACT_ABI_FILE", "")

    try:
        f = open(contractABIFile, "r")
        f.close()
    except FileNotFoundError:
        logger.error("Contract ABI file not found" % (contractABIFile,))
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

def SmartContractFactory():
    return SmartContract(os.getenv("RPC_URL"), os.getenv("CONTRACT_ADDRESS"), os.getenv("CONTRACT_ABI_FILE"))

class SmartContract():
    def __init__(self, rpcURL, contractAddress, contractABIFile):
        self.logger = logging.getLogger("SmartContract")
        self.logger.setLevel(logging.INFO)

        # check if the contractABIFile is a file that exists and throw if not
        try:
            f = open(contractABIFile, "r")
            f.close()
        except FileNotFoundError:
            self.logger.error("Contract ABI file not found" % (contractABIFile,))
            raise FileNotFoundError

        self.active = False
        self.rpcURL = rpcURL
        self.contractAddress = contractAddress
        self.contractABIFile = contractABIFile
        self.eventListenerThread = Thread(target=self.eventListener)

    def platformConnect(self, contract_address, geth_ip, geth_port, index):
        self.contract_address=contract_address
        self.ethclient = EthereumClient(ip=geth_ip, port=geth_port)
        self.getEthAccount(index)
        self.contract = ModicumContract.ModicumContract(index, self.ethclient, self.contract_address)
        self.platformListenerThread.start()
        return self.ethclient, self.contract

    def eventListener(self):
        self.active = True
        while self.active:
            events = self.contract.poll_events()
            # self.logger.info("poll contract events")
            for event in events:
                params = event['params']
                name = event['name']
                self.logger.info("{}({}).".format(name, params))
            self.wait()

    def stop(self):
        self.logger.info("Stop Client")
        self.active = False
        self.ethclient.exit()
        # self.dockerClient.close() #not required but unittest throws a warning if not used.
