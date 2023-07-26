import logging
import logging.config
import os
import subprocess
import textwrap
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
from .Enums import ResultStatus, Verdict, Party

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

    def register(self, account, arch, instructionPrice, bandwidthPrice, availabilityValue, verificationCount):
        self.logger.info("A: registerMediator")
        self.account = account
        txHash = self.ethclient.transact(
            self.ethclient.contract.functions.registerMediator(
                arch,
                instructionPrice,
                bandwidthPrice,
                availabilityValue,
                verificationCount
            ), {
                "from": self.account,
            },
        )

    def getJob(self, matchID, JO, execute):
        self.logger.info("🔵🔵🔵 RUN JOB NOW")
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
                result = subprocess.run(['bacalhau', 'create', '--wait', '--id-only', tmpfile], text=True, capture_output=True, check=True)
                jobID = result.stdout.strip()

                # extrac the CID of the result to report back
                listOutput = subprocess.run(['bacalhau', 'list', '--output', 'json', '--id-filter', jobID], text=True, capture_output=True, check=True)

                print(textwrap.dedent(f"""
                ---------------------------------------------------------------------------------------

                {listOutput.stdout}

                ---------------------------------------------------------------------------------------
                """))

                # load the listOutput string as a JSON object
                listOutputJSON = json.loads(listOutput.stdout)

                resultHash = listOutputJSON[0]['State']['Executions'][0]['PublishedResults']['CID']
                resultStatus = listOutputJSON[0]['State']['Executions'][0]['State']

                print(textwrap.dedent(f"""
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------

                {open(tmpfile).read()}

                https://dashboard.bacalhau.org/jobs/{jobID}

                Get stdout, status:
                docker exec -ti resource-provider bacalhau describe {jobID}

                Download results CID from IPFS:
                docker exec -ti resource-provider bacalhau get {jobID}

                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                """))

                describe = subprocess.run(['bacalhau', 'describe', jobID], text=True, capture_output=True).stdout
                print(textwrap.dedent(f"""
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------

                {describe}

                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                ---------------------------------------------------------------------------------------
                """))

                # before we return the hash - let's copy the results out from IPFS so we can serve them
                # from out embedded nginx container
                subprocess.run(['mkdir', '-p', '/tmp/lilypad-results'], text=True, capture_output=True, check=True)
                subprocess.run(['ipfs', '--repo-dir', '/root/.ipfs', 'get', resultHash], text=True, capture_output=True, check=True, cwd="/tmp/lilypad-results")

                return resultHash

        

        # self.postResult(matchID, JO.offerId, resultStatus, urix, resultHash, cpuTime, 0)
                
    def postResult(self, matchID, joid, resultHash):
        reason = Verdict.WrongResults.value
        if self.myMatches[matchID]['resHash'] == resultHash:
            reason = Verdict.CorrectResults.value
            self.logger.info("🟣🟣🟣🟣 ✅✅✅✅✅✅✅✅✅✅✅ mediation correct result")
        else:
            reason = Verdict.WrongResults.value
            self.logger.info("🟣🟣🟣🟣 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨 mediation wrong result")
        self.ethclient.transact(
            self.contract.functions.postMediationResult(
                matchID,
                joid,
                ResultStatus.Completed.value, 
                "",
                resultHash,
                reason,
                Party.ResourceProvider.value
            ), {
                "from": self.account,
            },
        )

    def CLIListener(self):
        pass

    def platformListener(self):
        self.active = True
        self.logger.info(f"poll contract events on {self.ethclient.contract_address}")
        while self.active:
            events = self.ethclient.poll_events()
            # self.logger.info(f"poll contract events, got {events}")
            for event in events:
                params = event['params']
                name = event['name']
                transactionHash = event['transactionHash']
                if name == "DebugUint" :
                    self.logger.info(name)
                    self.getReceipt(name, transactionHash)
                elif name == "MediatorRegistered" and self.account == params['addr']:
                    self.logger.info("🔴 MediatorRegistered: \n({}).".format(params))
                    self.logger.info("A: %s" %name)
                    self.getReceipt(name, transactionHash)
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                    self.registered = True
                elif name == "ResourceOfferPosted":
                    self.logger.info("🔴 ResourceOfferPosted: \n({}).".format(params))
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
                    self.logger.info("🔴 JobOfferPosted: \n({}).".format(params))
                    self.logger.info(name)
                    helper.storeJobOffer(event,self.job_offers)

                elif name == "Matched" and self.account == params['mediator']:
                    self.logger.info("🔴 Matched: \n({}).".format(params))
                    self.logger.info(name)

                    matchID = params['matchId']
                    joid = params['jobOfferId']
                    roid = params['resourceOfferId']
                    self.myMatches[matchID] = {
                        'joid': joid,
                        'roid': roid
                    }

                elif name == "ResultPosted" and params['matchId'] in self.myMatches:
                    self.logger.info("🔴 ResultPosted: \n({}).".format(params))
                    self.myMatches[params['matchId']]['resHash'] = params['hash']

                    joid = self.myMatches[matchID]['joid']
                    JO = self.job_offers[joid]
                    ijoid = JO.ijoid

                    roid = self.myMatches[matchID]['roid']
                    RO = self.resource_offers[roid]
                    iroid = RO.iroid


                elif name == "JobAssignedForMediation" and params['matchId'] in self.myMatches:
                    self.logger.info("🔴 JobAssignedForMediation: \n({}).".format(params))
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
                    resultHash = self.getJob(matchID, JO, True)

                    self.postResult(matchID, JO.offerId, resultHash)

                    self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "M" + str(self.index)},
                                          seriesname="state", value=1)

                elif name == "MediationResultPosted" and params['matchId'] in self.myMatches:
                    self.logger.info("🔴 MediationResultPosted: \n({}).".format(params))
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

                elif name == "EtherTransferred":
                    self.logger.info("🟡 EtherTransferred: \n({}).".format(params))

            self.wait()
