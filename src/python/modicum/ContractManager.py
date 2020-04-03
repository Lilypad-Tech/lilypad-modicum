import zmq
import logging
import sys
import os
import dotenv
from time import time, sleep
from threading import Thread
import hashlib
import json
from .EthereumClient import EthereumClient
from .Contract.ModicumContract import ModicumContract
from . import config as cfg
from . import helper
import datetime

import pprint


class ContractManager:
    def __init__(self, manager_ip,index):
        self.logger = logging.getLogger("ContractManager")
        self.logger.setLevel(logging.INFO)

        self.index = index
        
        # ch = logging.StreamHandler()
        # formatter = logging.Formatter("---%(name)s---:%(message)s")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.helper = helper.helper()

        self.manager_ip = manager_ip
        super(ContractManager, self).__init__()
        self.listenerThread = Thread(target=self.pollClients)

    def startEthClient(self,ip,port):
        self.ethclient = EthereumClient(ip=ip, port=port)
        self.logger.info("client: %s" %self.ethclient)

    def getEthAccount(self,index):
        response = self.ethclient.accounts()
        self.logger.debug("ethclient accounts: %s" %response)
        if "ERROR" not in response:
          self.account = response[index] # use the first owned address
          return self.account
        else:
          return "ERROR: Failed to fetch account"


    def pollClients(self):
        self.logger.info("Entering main function...")
        self.ctxt = zmq.Context()
        self.zmqclient = self.ctxt.socket(zmq.REP)
        self.zmqclient.bind("tcp://%s:10001" %self.manager_ip)
        self.poller = zmq.Poller()
        self.poller.register(self.zmqclient, zmq.POLLIN)
        # epoch = time() - START_INTERVAL * INTERVAL_LENGTH
        epoch = time()
        self.logger.info("Listening for clients...")
        self.listening = True
        while self.listening:
            socks = dict(self.poller.poll(1000))
            # self.logger.info("Polling")
            if self.zmqclient in socks and socks[self.zmqclient]:
                msg = self.zmqclient.recv_pyobj()
                if msg['request'] == "query_contract_address":
                    self.logger.info("query_contract_address() : %s" %msg["index"])
                    self.zmqclient.send_pyobj({'contract': self.contract_address, 'time': time() - epoch})
                    self.logger.info("contract_address sent")

                elif msg['request'] == "stop":
                    self.zmqclient.send_pyobj("Contract Manager Stopping")
                    self.stop()
                else:
                    self.logger.error("Unknown request: " + msg['request'])
                    self.zmqclient.send_pyobj("Unknown request!")

            try:
                self.helper.getPendingTx(self.ethclient)
            except :



    def stop(self):
        self.logger.info("Stop Contract Manager")
        self.listening = False
        self.ethclient.exit()
        # self.listenerThread.join()

    def deploy_contract(self,BYTECODE,TRANSACTION_GAS,verbose=False):
        self.logger.info("Y: Deploying contract...")

        gasEstimate = self.ethclient.command("eth_estimateGas", params=[{}], verbose=verbose)
        self.logger.info("Estimate of gas requirement to submit contract: %s" %gasEstimate)

        # gasEstimate = self.ethclient.command("eth_estimateGas", params=[{'data': BYTECODE, 'from':self.account, 'gas':'0x2C68AF0BB140000'}], verbose=verbose)

        self.logger.info("Estimate of gas requirement to submit contract: %s" %gasEstimate)


        gasEstimate = self.ethclient.command("eth_estimateGas", params=[{'data': BYTECODE, 'from':self.account, 'gas':TRANSACTION_GAS}], verbose=verbose)

        self.logger.info("Estimate of gas requirement to submit contract: %s" %gasEstimate)

        txHash = self.ethclient.command("eth_sendTransaction", params=[{'data': BYTECODE, 'from': self.account, 'gas': TRANSACTION_GAS}], verbose=verbose)

        receipt = helper.wait4receipt(self.ethclient,txHash,getReceipt=True)
        self.contract_address = receipt['contractAddress']
        self.contract = ModicumContract(self.index, self.ethclient, self.contract_address)
        self.logger.info("Contract address: " + self.contract_address)

        self.logger.info("Y: Contract mined")
        return self.contract_address

    def updateParams(self):
        ### Updating environment ###
        reactionDeadline = int(os.getenv('ReactionDeadline', '86400'))
        self.logger.info(f'Updating ReactionDeadline to {reactionDeadline}')
        txHash = self.contract.setReactionDeadline(self.account,  True, reactionDeadline)
        self.logger.info("Transaction receipt: " + txHash)

        receipt = helper.wait4receipt(self.ethclient,txHash,getReceipt=True)
        self.logger.info(f'ReactionDeadline mined')
        self.helper.logEvent(self.index, "reactionDeadlineSet", self.ethclient, txHash)

        self.penaltyRate = int(os.getenv('PenaltyRate', '64'))
        self.logger.info(f'Updating penaltyRate to {self.penaltyRate}')

        txHash = self.contract.setPenaltyRate(self.account,  True, self.penaltyRate)

        helper.wait4receipt(self.ethclient,txHash,getReceipt=True)
        self.logger.info(f'PenaltyRate mined')
        self.helper.logEvent(self.index, "penaltyRateSet", self.ethclient, txHash)

        events = self.contract.poll_events()
        print("EVENTS: %s" %events)
        for event in events:
            params = event['params']
            name = event['name']
            transactionHash = event['transactionHash']
            self.logger.info("{}({}).".format(name, params))


        ### Done ###

    def connect(self,geth_ip,geth_port,index):
        self.ethclient = EthereumClient(ip=geth_ip, port=geth_port)
        connected = False
        while not connected:
            response = self.getEthAccount(index)
            self.logger.info(response)
            if "ERROR" not in response:
                connected = True
            sleep(1)
        self.logger.info("Account address is : %s" %response)
        return response
            
    def testrun(self):
        contractjson = {}
        contractjson['contractAddress'] = "0xecde4dbcec737fb9d99edb86d69aff540da7e384"
        self.contract_address = contractjson['contractAddress']

        self.contract = ModicumContract(self.ethclient, self.contract_address, self.index)

        self.updateParams()
        # #--------------------------------------------------------------------
        # # Service Requests
        # #--------------------------------------------------------------------
        self.listenerThread.start()


    def run(self,BYTECODE,TRANSACTION_GAS,verbose):
        # path = dotenv.find_dotenv('.env', usecwd=True)
        # dotenv.load_dotenv(path)

        #--------------------------------------------------------------------
        # Get Contract Address.
        #--------------------------------------------------------------------
        contractHash = hashlib.sha256(BYTECODE.encode()).hexdigest()
        print(contractHash)
        contractjson = {}
        
        try:  
            with open ('contract.json','r') as f : 
                try:
                    contractjson = json.load(f)
                except json.decoder.JSONDecodeError:
                    print("json is empty")
                    contractjson['hash'] = None
        except FileNotFoundError:
            print("File does not exist")
            contractjson['hash'] = None
            

        if contractjson['hash'] != contractHash:
            with open('contract.json','w') as f : 
                print("write json")
                contractjson['hash'] = contractHash 

                contractjson['contractAddress'] = self.deploy_contract(BYTECODE,TRANSACTION_GAS,verbose) 

                print("\n")  
                print(contractjson)     
                print("\n")
                json.dump(contractjson,f)              
        else:
            print("Contract has not changed")
            self.contract_address = contractjson['contractAddress']

            self.contract = ModicumContract(self.index, self.ethclient, self.contract_address)

            
        self.updateParams()
        #--------------------------------------------------------------------
        # Service Requests
        #--------------------------------------------------------------------
        self.listenerThread.start()
