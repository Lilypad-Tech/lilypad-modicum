import logging
import logging.config
import os
import subprocess
import docker.errors
from . import DockerWrapper
from .PlatformClient import PlatformClient
from .Modules import get_bacalhau_jobspec
from . import PlatformStructs as Pstruct
from . import helper
import dotenv
import time
import traceback
import json
import datetime
import tempfile
import yaml



class Mediator(PlatformClient):
    def __init__(self, index,sim):
        super().__init__()
        self.logger = logging.getLogger("Mediator")
        # logging.config.fileConfig(os.path.dirname(__file__)+'/Modicum-log.conf')
        self.logger.setLevel(logging.INFO)

        # ch = logging.StreamHandler()
        # formatter = logging.Formatter("---%(name)s---: \n%(message)s\n\r")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.job_offers = {}
        self.resource_offers = {}
        self.registered = False

        self.myMatches = {}

        path = dotenv.find_dotenv('.env', usecwd=True)
        dotenv.load_dotenv(path)

        self.index = index
        self.sim = sim

        if index >= 0:
            self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "M" + str(self.index)},
                           seriesname="state", value=1)

    def test(self, value):
        self.logger.info("run test")
        exitcode = self.contract.test(self.account,  True, value)
        return exitcode

    def register(self, account, arch, instructionPrice, bandwidthPrice, availabilityValue, verificationCount):
        self.logger.info("A: registerMediator")
        self.account = account
        self.contract.registerMediator(self.account, True, arch, instructionPrice, bandwidthPrice, availabilityValue, verificationCount)

    def getJob(self, matchID, JO, execute):
        JID = JO.jobCreator
        ijoid = JO.ijoid
        uri = JO.uri
        extras = JO.extras

        extrasData = json.loads(extras)
        bacalhauJobSpec = get_bacalhau_jobspec(
            extrasData["template"],
            extrasData["params"]
        )

        _DIRIP_ = os.environ.get('DIRIP')
        _DIRPORT_ = os.environ.get('DIRPORT')
        _KEY_ = os.environ.get('pubkey')
        _SSHKEY_ = os.environ.get('sshkey')
        _SSHPORT_ = os.environ.get('SSHPORT')
        _WORKPATH_ = os.environ.get('WORKPATH')
        statusJob=0
        cpuTime=0
        endStatus="Completed"
        input_exists=False
        image_exits=False
        resultHash = "0000000000000000000000000000000000000000000000000000000000000000"
        # tag,name = uri.split('_')
        urix = uri+"_"+str(ijoid)

        # write bacalhauJobSpec to yaml file in temporary directory
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpfile = tmpdirname + "/job.yaml"
            with open(tmpfile, 'w') as f:
                yaml.dump(bacalhauJobSpec, f)
                f.close()

                # RUN BACALHAU JOB AND GET THE ID
                result = subprocess.run(['bacalhau', 'create', '--wait', '--id-only', tmpfile], text=True, capture_output=True)
                jobID = result.stdout.strip()

                # extrac the CID of the result to report back
                listOutput = subprocess.run(['bacalhau', 'list', '--output', 'json', '--id-filter', jobID], text=True, capture_output=True)

                # load the listOutput string as a JSON object
                listOutputJSON = json.loads(listOutput.stdout)

                resultHash = listOutputJSON[0]['State']['Executions'][0]['PublishedResults']['CID']

                print(f"""
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------

                {open(tmpfile).read()}

                https://dashboard.bacalhau.org/jobs/{jobID}

                Get stdout, status:
                docker exec -ti lilypad-node bacalhau describe {jobID}

                Download results CID from IPFS:
                docker exec -ti lilypad-node bacalhau get {jobID}

                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                """)

                describe = subprocess.run(['bacalhau', 'describe', jobID], text=True, capture_output=True).stdout
                print(f"""
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------

                {describe}

                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                """)

                self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
                
    def postResult(self, matchID, joid, endStatus, uri, resultHash, cpuTime, bandwidthUsage):
        resultHash_int = int(resultHash, 16)

        if endStatus!=0:
            if self.account:
                resultHash_int = int(resultHash, 16)

                self.logger.info("N: postMediationResult: %s, JC at fault = %s" %(endStatus,uri))
                self.logger.info("Hash mismatch")
                reason = 'InvalidResultStatus'
                faultyParty = 'JobCreator'
        else :
            if self.myMatches[matchID]['resHash'] == resultHash_int:
                self.logger.info("N: postMediationResult: %s, JC at fault = %s" %(endStatus,uri))
                reason = 'CorrectResults'
                faultyParty = 'JobCreator'
            else:
                self.logger.info("N: postMediationResult: %s, RP at fault = %s" %(endStatus,uri))
                reason = 'WrongResults'
                faultyParty = 'ResourceProvider'
                
        
        self.contract.postMediationResult(self.account, True, matchID, joid, endStatus, 
                                          uri, resultHash_int, cpuTime, 0, 
                                          reason, faultyParty)
        

    def CLIListener(self):
        pass

    def platformListener(self):
        self.active = True
        self.logger.info(f"poll contract events on {self.contract.address}")
        while self.active:
            events = self.contract.poll_events()
            # self.logger.info(f"poll contract events, got {events}")
            for event in events:
                params = event['params']
                name = event['name']
                transactionHash = event['transactionHash']
                self.logger.info("🔴 mediator event: {}\n({}).".format(name, params))
                if name == "DebugUint" :
                    self.logger.info(name)
                    self.getReceipt(name, transactionHash)
                elif name == "MediatorRegistered" and self.account == params['addr']:
                    self.logger.info("A: %s" %name)
                    self.getReceipt(name, transactionHash)
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                    self.registered = True
                elif name == "ResourceOfferPosted":
                    self.logger.info(name)
                    offer = Pstruct.ResourceOffer(
                                        params['offerId'],
                                        params['addr'],
                                        params['instructionPrice'],
                                        params['instructionCap'],
                                        params['memoryCap'],
                                        params['localStorageCap'],
                                        params['bandwidthCap'],
                                        params['bandwidthPrice'],
                                        params['deposit'],
                                        params['iroid']
                                        )
                    self.resource_offers[params['offerId']] =  offer

                elif "JobOfferPosted" in name: 
                    self.logger.info(name)
                    helper.storeJobOffer(event,self.job_offers)

                elif name == "Matched" and self.account == params['mediator']:
                    
                    self.logger.info(name)

                    matchID = params['matchId']
                    joid = params['jobOfferId']
                    roid = params['resourceOfferId']
                    self.myMatches[matchID] = {
                        'joid': joid,
                        'roid': roid
                    }

                elif name == "ResultPosted" and params['matchId'] in self.myMatches:
                        
                        self.myMatches[params['matchId']]['resHash'] = params['hash']

                        joid = self.myMatches[matchID]['joid']
                        JO = self.job_offers[joid]
                        ijoid = JO.ijoid

                        roid = self.myMatches[matchID]['roid']
                        RO = self.resource_offers[roid]
                        iroid = RO.iroid


                elif name == "JobAssignedForMediation" and params['matchId'] in self.myMatches:
                    self.logger.info(name)
                    self.getReceipt(name, transactionHash)
                    
                    matchID = params['matchId']
                    joid = self.myMatches[matchID]['joid']
                    JO = self.job_offers[joid]
                    tag = JO.uri 
                    ijoid = JO.ijoid

                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid)

                    self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "M" + str(self.index)},
                                          seriesname="state", value=2)
                    self.getJob(matchID, JO, True)
                    self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "M" + str(self.index)},
                                          seriesname="state", value=1)

                elif name == "MediationResultPosted" and params['matchId'] in self.myMatches:

                    matchID = params['matchId']
                    joid = self.myMatches[matchID]['joid']
                    JO = self.job_offers[joid]
                    ijoid = JO.ijoid

                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid)

                    self.logger.info("N: %s = %s" %(name,params['uri']))
                    self.logger.info("N: %s = %s" %(name,ijoid))
                    self.getReceipt(name, transactionHash)

                elif name == "DebugString":
                    self.logger.info(params["str"])
                    self.getReceipt(name, transactionHash)

            self.wait()
