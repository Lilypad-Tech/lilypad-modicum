# import os
import zmq
import logging
from threading import Thread
import time
import dotenv
import os
import subprocess
# logging.basicConfig(format='--%(name)s--: %(message)s', level=logging.INFO)
from .Contract import ModicumContract as ModicumContract
from .DirectoryClient import DirectoryClient
from . import DockerWrapper
from .EthereumClient import EthereumClient

import influxdb
import requests
from . import helper


class PlatformClient():
    def __init__(self):
        # logging.basicConfig(format='-A-%(name)s-A-: %(message)s', level=logging.INFO)

        self.logger = logging.getLogger("PlatformClient")
        self.logger.setLevel(logging.INFO)
        
        # ch = logging.StreamHandler()
        # # formatter = logging.Formatter("---%(name)s---: \n%(message)s\n\r")
        # formatter = logging.Formatter("---%(name)s---:%(message)s")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.account = None
        self.active = False
        self.platformListenerThread = Thread(target=self.platformListener)

        path = dotenv.find_dotenv('.env', usecwd=True)
        dotenv.load_dotenv(path)

        influx_ip = os.environ.get('INFLUX')
        print(influx_ip)
        db = "collectd_db"
        self.client = influxdb.InfluxDBClient(influx_ip, 8086, db)
        self.client.switch_database("collectd")

        self.helper = helper.helper()

    def logInflux(self, now, tag_dict, seriesname, value):
        records = []

        floatvalue = None

        if value is not None:
            try:
                floatvalue = float(value)
            except:
                floatvalue = None

        if floatvalue is not None:
            # ---------------------------------------------------------------------------------
            record = {"time": now,
                      "measurement": seriesname,
                      "tags": tag_dict,
                      "fields": {"value": floatvalue},
                      }
            records.append(record)
        self.logger.info("writing: %s" % str(records))
        try:
            res = self.client.write_points(records)  # , retention_policy=self.retention_policy)
        except requests.exceptions.ConnectionError as e:
            self.logger.warning("CONNECTION ERROR %s" % e)
            self.logger.warning("try again")



    def startCLIListener(self, cliport="7654"):
        self.cliSocket = zmq.Context().socket(zmq.REP)
        self.logger.info("cli Port: %s" %cliport)
        self.cliSocket.bind("tcp://*:%s" %cliport)
        self.DC = DirectoryClient() #used by JC and RP
        self.dockerClient = DockerWrapper.getDockerClient() #used by JC and RP
        self.CLIListenerThread = Thread(target=self.CLIListener)
        self.CLIListenerThread.start()

    def CLIListener(self):
        active = True
        while active:
            msg = self.cliSocket.recv_pyobj()
            self.logger.info("cli received: %s" %msg)
            if msg['request'] == "stop":
                active = False
                self.cliSocket.send_pyobj("stopping...")
                self.stop()
                # self.cliSocket.close()
            # elif msg['request'] == "publish":
            #     responseJC = self.DC.getPermission(msg["host"],msg["port"],msg["ijoid"],msg["job"],msg["pubkey"])
            #     self.DC.publishData(msg["host"],msg["sftport"],msg["ijoid"],msg["job"],msg["localpath"],msg["sshpath"])
            #     self.cliSocket.send_pyobj("data published")
            # elif msg["request"] == "getJob":
            #     responseRP = self.DC.getPermission(msg["host"],msg["port"],msg["iroid"],msg["job"],msg["pubkey"])
            #     self.DC.getData(msg["host"],msg["sftport"],msg["iroid"],msg["ijoid"],msg["job"],msg["localpath"],msg["sshpath"])
            #
            #     DockerWrapper.buildImage(self.dockerClient,msg["localpath"]+"/"+msg["job"],msg["job"])
            #
            #     # DockerWrapper.runContainer(self.dockerClient, msg["job"], "thisJob", msg["mounts"], msg["environment"])
            #     DockerWrapper.runContainer(self.dockerClient, msg["job"], "thisJob", msg["input"], msg["output"],msg["appinput"],msg["appoutput"],msg["perf_enabled"])
            #
            #
            #     self.DC.publishData(msg["host"],msg["sftport"],msg["iroid"],msg["job"],msg["localpath"],msg["sshpath"])
            #
            #     self.cliSocket.send_pyobj("result published")
            #
            # elif msg["request"] == "getResult":
            #     # responseJC = self.DC.getPermission(msg["host"],msg["port"],msg["ijoid"],msg["job"],msg["pubkey"])
            #     self.DC.getData(msg["host"],msg["sftport"],msg["ijoid"],msg["iroid"],msg["job"],msg["localpath"],msg["sshpath"])
            #     self.cliSocket.send_pyobj("got result")

    def platformConnect(self, manager_ip, geth_ip, geth_port,index):
        self.managerSocket = zmq.Context().socket(zmq.REQ)
        self.managerSocket.connect(f"tcp://{manager_ip}:10001")
        self.contract_address=self.query_contract_address(index)
        self.ethclient = EthereumClient(ip=geth_ip, port=geth_port)
        self.getEthAccount(index)
        self.contract = ModicumContract.ModicumContract(index, self.ethclient, self.contract_address)
        self.platformListenerThread.start()
        return self.ethclient,self.contract

    def getEthAccount(self,index):
        response = self.ethclient.accounts()
        # self.logger.info("ALL ACCOUNTS: %s" %response)
        if "ERROR" not in response:
          self.account = response[index] # use the first owned address
          self.logger.info("My account: %s" %self.account)
          return self.account
        else:
          return "ERROR: Failed to fetch account"

    # def platformDisconnect(self):
    #     msg = {
    #       'request': "stop"
    #     }
    #     self.managerSocket.send_pyobj(msg)
    #     response = self.managerSocket.recv_pyobj()
    #     self.logger.info("manager Response: %s" %response)
    #     self.ethclient.exit()

    def query_contract_address(self,index):
      msg = {
        'request': "query_contract_address",
        'index' : index
      }
      self.logger.info("Z: Get Contract address")
      self.logger.info("Message to manager: {}".format(msg))
      self.managerSocket.send_pyobj(msg)
      response = self.managerSocket.recv_pyobj()
      self.contract_address = response['contract']
      self.logger.info("Contract address: " + self.contract_address)
      self.logger.info("Z: Got Contract address")
      return self.contract_address

    def wait(self):
        time.sleep(1)

    def platformListener(self):
        self.active = True
        while self.active:
            events = self.contract.poll_events()
            # self.logger.info("poll contract events")
            for event in events:
                params = event['params']
                name = event['name']
                self.logger.info("{}({}).".format(name, params))
            self.wait()

    def getReceipt(self, name, transactionHash):
        receipt = self.ethclient.command("eth_getTransactionReceipt", params=[transactionHash])
        self.logger.info("%s gasUsed: %s" %(name, receipt['gasUsed']))
        self.logger.info("%s cumulativeGasUsed: %s" %(name, receipt['cumulativeGasUsed']))

    def stop(self):
        self.logger.info("Stop Client")
        self.active = False
        self.ethclient.exit()
        # self.dockerClient.close() #not required but unittest throws a warning if not used.
