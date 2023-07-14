import logging.config
import os
import subprocess
import time
import traceback
import random
import json
import textwrap
import dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from .Modules import get_bacalhau_jobprice
from . import DockerWrapper
from . import PlatformStructs as Pstruct
from .PlatformClient import PlatformClient
from . import helper
from web3 import Web3

import datetime

def should_mediate():
    mediation_chance = os.getenv('MEDIATION_CHANCE_PERCENT', 20)
    if(mediation_chance > 100):
        mediation_chance = 100
    return random.randint(1, 100) <= int(mediation_chance)

class JobFinished(Exception):
    pass


class JobCreator(PlatformClient):
    def __init__(self, index=0, sim=False):
        super().__init__()
        self.logger = logging.getLogger("JobCreator")
        # logging.config.fileConfig(os.path.dirname(__file__)+'/Modicum-log.conf')
        self.logger.setLevel(logging.INFO)
        
        # ch = logging.StreamHandler()
        # formatter = logging.Formatter("---%(name)s---:%(message)s")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.job_offers = {}
        self.resource_offers = {}
        self.matches={}
        self.registered = False

        path = dotenv.find_dotenv('.env', usecwd=True)
        dotenv.load_dotenv(path)

        self.verificationChance = 0.10
        self.reject={}

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        self.lastId = 0
        self.penaltyRate = None
        self.mediator = None
        self.ijoid = 0

        self.index = index
        self.sim = sim

        self.jobsPending = 0

        self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "JC"+str(self.index)},
                              seriesname="state", value=1)
        
        self.state = "Starting"
        self.status = ""
        self.finished = False


    def register(self, account):
        self.logger.info("A: registerJobCreator")
        self.account = account
        txHash = self.ethclient.contract.functions.registerJobCreator().transact({
            "from": self.account,
        })
        return 0

    def addMediator(self,account,mediator):
        self.logger.info("B: jobCreatorAddTrustedMediator")
        txHash = self.ethclient.contract.functions.jobCreatorAddTrustedMediator(mediator).transact({
            "from": self.account,
        })
        return 0

    def getResult(self,user, tag,name,joid, ijoid, resultID,RID, hash):
        _DIRIP_ = os.environ.get('DIRIP')
        _DIRPORT_ = os.environ.get('DIRPORT')
        _SSHKEY_ = os.environ.get('sshkey')
        _SSHPORT_ = os.environ.get('SSHPORT')
        _WORKPATH_ = os.environ.get('WORKPATH')

        remote_user = self.DC.getUsername(_DIRIP_, _DIRPORT_, RID)

        localPath = "%s/%s" %(_WORKPATH_, tag)
        os.makedirs(localPath, exist_ok=True) #HACK

        self.logger.info("K: DC getResult = %s" %joid)

        self.DC.getResult(host=_DIRIP_,sshport=_SSHPORT_,user=user,
                          remote_user=remote_user,tag=tag,name=name,
                          ijoid=ijoid,localPath=localPath,sshpath=_SSHKEY_)
        self.logger.info("K: DC gotResult = %s" %ijoid)

        # TODO check hash param is the same as DC.getData's hash

        self.logger.info("F: acceptResult = %s: " %joid)
        txHash = self.ethclient.contract.functions.acceptResult(resultID, joid).transact({
            "from": self.account,
        })

        return 0



    def publish(self,path,tag,name,ijid):
        _DIRIP_ = os.environ.get('DIRIP')
        _DIRPORT_ = os.environ.get('DIRPORT')
        _KEY_ = os.environ.get('pubkey')
        _SSHPORT_ = os.environ.get('SSHPORT')
        _SSHKEY_ = os.environ.get('sshkey')

        if self.sim:
            return 0

        self.logger.info("L: Requesting Permission to publish")

        msg = self.DC.getPermission(_DIRIP_, _DIRPORT_, self.account, tag, _KEY_)

        self.user = msg['user']
        self.groups = msg['groups']

        self.logger.info("my username: %s" %self.user)
        self.logger.info("L: permission granted? : %s" %(msg['exitcode']==0))
        

        if msg['exitcode'] == 0:
            self.logger.info("publish data")
            self.DC.publishData(_DIRIP_,_DIRPORT_,self.user,path,tag,name,ijid, sshpath=_SSHKEY_)
            return 0
        else:
            return 1
        

    def runJob(self,tag,jobname):
        '''this is broken, and not called currently'''

        if self.sim:
            return 0
        
        _WORKPATH_ = os.environ.get('WORKPATH')
        localPath = "%s/%s/" %(_WORKPATH_, tag)
        
        xdictPath = localPath+name+str(ijoid)+"/"+name+".json"

        self.logger.info("xdictPath: %s" %xdictPath)
        with open(xdictPath) as f:
            xdict = json.load(f)

        self.logger.info("Starting Docker for job = %s" %ijoid)
        container = DockerWrapper.runContainer(self.dockerClient, tag, jobname, xdict)

    def runJob_old(self, tag, jobname):
        _WORKPATH_ = os.environ.get('WORKPATH')
        input = "%s/%s/input" %(_WORKPATH_,tag)
        output = "%s/%s/output" %(_WORKPATH_,tag)
        appinput = "/app/input"
        appoutput = "/app/output"
        try:
            container = DockerWrapper.runContainer(self.dockerClient, tag, jobname, input, output,appinput,appoutput)
        except docker.errors.DockerException as err:
            self.logger.info("error is : %s" %err)

    def timeout(self, matchId):

        joid = self.matches[matchID].jobOfferId
        ijoid = self.job_offers[joid].ijoid

        self.logger.info("O: timeout = %s" %(name, ijoid))   
        self.logger.info(f'Match {matchId} timed out.')

        txHash = self.ethclient.contract.functions.timeout(matchId, joid).transact({
            "from": self.account,
        })

    def scheduleTimeout(self, matchID, deadline_ms):
        self.logger.info("now: %s" %time.time())
        deadline_s = deadline_ms/1000
        self.logger.info("deadline: %s" %deadline_s)
        self.logger.info("type(deadline): %s" %type(deadline_s))

        to_run = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(deadline_s))
        self.scheduler.add_job(self.timeout, 'date', id=str(matchID), run_date=to_run, args=[matchID])

    def CLIListener(self):
        active = True
        while active:
            msg = self.cliSocket.recv_pyobj()
            self.logger.info("cli received: %s" %msg)
            if msg['request'] == "stop":
                active = False
                self.cliSocket.send_pyobj("stopping...")
                self.stop()
            elif msg['request'] == "addMediator":
                mediator = msg["mediator"]
                if self.account:
                    exitcode = self.addMediator(self.account, mediator)
                    self.cliSocket.send_pyobj("Mediator added? %s" %(exitcode==0) )
                else:
                    exitcode = 1
                    self.cliSocket.send_pyobj("Mediator added? %s, account is %s" %(exitcode==0, self.account) )

            elif msg['request'] == "publish":
                exitcode = self.publish(                            
                            msg["path"],
                            msg["tag"],
                            msg["name"]
                            )
                self.logger.info("published? : %s" %(exitcode==0))
                self.cliSocket.send_pyobj("published? : %s" %(exitcode==0))
            
            elif msg['request'] == "post":
                while not self.penaltyRate or not self.mediator:
                    time.sleep(1)
                self.postOffer(msg)
            
            elif msg['request'] =="getResult":
                exitcode = self.getResult(
                                msg["user"],
                                msg["tag"],
                                msg["resultID"],
                                msg["RID"],
                                    0 # TODO this is the expected hash of result.
                                )
                self.cliSocket.send_pyobj("got result? : %s" %(exitcode==0))

    def platformListener(self):
        self.active = True
        while self.active:
            events = self.ethclient.poll_events()
            # self.logger.info(f"poll contract events, got {events}")
            for event in events:
                params = event['params']
                name = event['name']
                # self.logger.info("{}({}).".format(name, params))
                if name == "JobCreatorRegistered" and self.account == params['addr']:
                    self.state = "JobCreatorRegistered"
                    self.logger.info("🔴 JobCreatorRegistered: \n({}).".format(params))
                    self.penaltyRate = params['penaltyRate']
                    self.registered = True
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                    self.logger.info("A: %s PenaltyRate : %s" %(name, self.penaltyRate))
                elif name == "JobCreatorAddedTrustedMediator" and self.account == params['addr']:
                    self.state = "JobCreatorAddedTrustedMediator"
                    self.logger.info("🔴 JobCreatorAddedTrustedMediator: \n({}).".format(params))
                    self.mediator = params['mediator']
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                    self.logger.info("B: %s" %name)
                elif name == "ResourceOfferPosted":
                    self.state = "ResourceOfferPosted"
                    self.logger.info("🔴 ResourceOfferPosted: \n({}).".format(params))
                    self.logger.info("%s" %name) 
                    helper.storeResourceOffer(event,self.resource_offers)           

                elif "JobOfferPosted" in name and self.account == params['addr']:   
                        self.logger.info("🔴 {}: \n({}).".format(name, params))
                        if "One" in name: 
                            self.state = "JobOfferPostedOne"
                            self.ijoid = params["ijoid"]
                            # self.logger.info("D: %s = %s" %(name,self.ijoid)) 
                            self.logger.info("D: %s offerId = %s" %(name,params["offerId"])) 
                        elif "Two"  in name and self.ijoid:   
                            self.state = "JobOfferPostedTwo"
                            # self.logger.info("D: %s = %s" %(name,self.ijoid)) 
                            self.logger.info("D: %s offerId = %s" %(name,params["offerId"])) 
                        
                        self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=params["offerId"], ijoid=self.ijoid)
                        helper.storeJobOffer(event,self.job_offers)


                elif name == "Matched":
                    self.state = "Matched"
                    self.logger.info("🔴 Matched: \n({}).".format(params))
                    joid = params['jobOfferId']
                    if joid in self.job_offers:
                        self.logger.info("%s matchId= %s" % (name, params['matchId']))
                        self.logger.info("%s offerId= %s" % (name, params['jobOfferId']))
                        self.logger.info("Job offer %s = %s" %(name, params['jobOfferId']))
                        self.logger.info("Resource offer %s = %s" %(name, params['resourceOfferId']))

                        matchID = params["matchId"]
                        match = Pstruct.Match(
                            params["jobOfferId"], params["resourceOfferId"], params["mediator"]
                        )
                        self.matches[matchID] = match


                        completionDeadline = self.job_offers[params['jobOfferId']].completionDeadline
                        self.logger.info("Job offer completionDeadline: %s" %completionDeadline)
                        self.logger.info("now: %s" %time.time())
                        # self.scheduleTimeout(matchID, completionDeadline)


                elif name == "ResultPosted":
                    self.logger.info("🔴 ResultPosted: \n({}).".format(params))
                    if params["matchId"] in self.matches:
                        matchID = params["matchId"]
                        uri = params["uri"]
                        self.logger.info("uri = %s" %(uri))                        
                        resultId = params["resultId"]
                        joid = self.matches[matchID].jobOfferId
                        ijoid = self.job_offers[joid].ijoid
                        roid = self.matches[matchID].resourceOfferId
                        # iroid = self.resource_offers[roid].iroid
                        # RID = self.resource_offers[roid].resourceProvider
                        
                        self.logger.info("%s Job = %s" %(name, ijoid))
                        self.logger.info("%s Resource = %s" %(name, roid))

                        self.logger.info("result status: %s" %params["status"])
                        self.logger.info("result status type: %s" %type(params["status"]))

                        if(should_mediate()):
                            txHash = self.ethclient.contract.functions.rejectResult(resultId).transact({
                                "from": self.account,
                            })
                        else:
                            txHash = self.ethclient.contract.functions.acceptResult(resultId, joid).transact({
                                "from": self.account,
                            })
                            self.state = "ResultsPosted"
                            self.status = f"https://ipfs.io/ipfs/{params['hash']}"

                elif name == "ResultReaction":
                    self.state = "ResultsReaction"
                    self.logger.info("🔴 ResultReaction: \n({}).".format(params))
                    if params["matchId"] in self.matches:
                        matchID = params["matchId"]

                        self.logger.info("show matches: %s" % (self.matches))
                        self.logger.info("matchID: %s" %matchID)

                        joid = self.matches[matchID].jobOfferId
                        ijoid = self.job_offers[joid].ijoid

                        self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid)

                        self.logger.info("F: %s = %s" %(name, ijoid))
                        

                elif name == "MatchClosed":
                    self.state = "MatchClosed"
                    self.logger.info("🔴 MatchClosed: \n({}).".format(params))
                    if params["matchId"] in self.matches:
                        matchID = params["matchId"]
                        joid = self.matches[matchID].jobOfferId
                        ijoid = self.job_offers[joid].ijoid
                        roid = self.matches[matchID].resourceOfferId
                        # iroid = self.resource_offers[roid].iroid

                        self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid)

                        self.jobsPending -= 1

                        self.helper.logInflux(now=datetime.datetime.now(), 
                                              tag_dict={"aix":self.index, "ijoid":ijoid, "event":name},
                                              seriesname="jobsPending",  
                                              value=self.jobsPending)

                        self.logger.info("Q: %s joid = %s" %(name, joid))
                        self.logger.info("Q: %s ijoid = %s" %(name, ijoid))
                        self.logger.info("Q: %s roid = %s" %(name, roid))
                        self.status = f"Released deposit of {Web3.from_wei(self.deposit, 'ether')} ETH to compute provider"

                elif name == "MediationResultPosted":
                    self.state = "MediationResultPosted"
                    self.logger.info("🔴 MediationResultPosted: \n({}).".format(params))
                    if params["matchId"] in self.matches:
                        matchID = params["matchId"]
                        joid = self.matches[matchID].jobOfferId
                        ijoid = self.job_offers[joid].ijoid
                        roid = self.matches[matchID].resourceOfferId
                        iroid = self.resource_offers[roid].iroid

                        self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid)
                
                elif name == "JobAssignedForMediation":
                    self.state = "JobAssignedForMediation"
                    self.logger.info("🔴 JobAssignedForMediation: \n({}).".format(params))
                    if params["matchId"] in self.matches:
                        self.logger.info("M: %s = %s" %(name, params["matchId"]))
                        matchID = params["matchId"]
                        joid = self.matches[matchID].jobOfferId
                        ijoid = self.job_offers[joid].ijoid
                        roid = self.matches[matchID].resourceOfferId
                        iroid = self.resource_offers[roid].iroid

                        self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid, value=.5)

                        self.logger.info("M: %s Match = %s" % (name, matchID))
                        self.logger.info("M: %s Job = %s" %(name, ijoid))
                        self.logger.info("M: %s Resource = %s" %(name, iroid))

                elif name == "EtherTransferred":
                    # TODO: We need an explicit state machine :-(
                    if self.state == "ResourceOfferPosted":
                        self.state = "Finished"
                        self.finished = True
                    else:
                        self.state = "EtherTransferred"
                    self.logger.info("🟡 EtherTransferred: \n({}).".format(params))


            self.wait()

    def postLilypadOffer(self, template, params):

        self.jobsPending += 1

        msg = {
          "ijoid":round(time.time()*1000),
          "cpuTime":800000,
          "bandwidthLimit":100,
          "instructionMaxPrice":1,
          "bandwidthMaxPrice":1,
          "completionDeadline":999999999999,
          "matchIncentive":1,
          "firstLayerHash":113999295367852254009166015506792353752063354354430764033672538180027823374984,
          "ramLimit":100,
          "localStorageLimit":1000,
          "uri":1,
          "directory":"0xc590dd7eed9f093d88d2f3c894b769c746bc8c9b",
          "hash":66153838227408534191608590763201001504128600065912625980963590518282769258064,
          "arch":"amd64"
        }

        # self.logger.info("cpuTime: %s Type: %s" %(msg["cpuTime"],type(msg["cpuTime"])))
        # self.logger.info("instructionMaxPrice: %s Type: %s" %(msg["instructionMaxPrice"],type(msg["instructionMaxPrice"])))
        # self.logger.info("bandwidthLimit: %s Type: %s" %(msg["bandwidthLimit"],type(msg["bandwidthLimit"])))
        # self.logger.info("bandwidthMaxPrice: %s Type: %s" %(msg["bandwidthMaxPrice"],type(msg["bandwidthMaxPrice"])))
        # self.logger.info("self.penaltyRate: %s Type: %s" %(self.penaltyRate,type(self.penaltyRate)))
        # self.logger.info("arch: %s Type: %s" %(msg['arch'],type(msg['arch'])))

        # make a JSON string from a single object that has template and params
        # as attributes
        jsonData = json.dumps({
          "template": template,
          "params": params
        })

        # deposit = (msg["cpuTime"]*msg["instructionMaxPrice"] +
        #            msg["bandwidthLimit"]*msg["bandwidthMaxPrice"])*self.penaltyRate

        # send the cost of the job

        deposit = self.ethclient.contract.functions.getModuleCost().call(template)
        self.deposit = deposit

        self.status = f"Sending deposit of {Web3.from_wei(self.deposit, 'ether')} ETH to contract"

        self.logger.info("🔵🔵🔵 post job offer")
        txHash = self.ethclient.contract.functions.postJobOfferPartOne(
            msg['ijoid'],
            msg['cpuTime'],
            msg['bandwidthLimit'],
            msg['instructionMaxPrice'],
            msg['bandwidthMaxPrice'],
            msg['completionDeadline'],
            msg['matchIncentive']
        ).transact({
          "from": self.account,
          "value": deposit,
        })

        self.logger.info("D: postJobOfferPartOne = %s" % (txHash,))

        # int,int,int,int,str,int,str,str = what python saw
        # uint256,uint256,uint256,bytes32,address,uint256,uint8,string = what it saw in the contract
        #  `int,int,int,int,str,int,str,str`
        # ['postJobOfferPartTwo(,,,,,,,)'
        # uint256,uint256,uint256,bytes32,address,uint256,uint8,string
        """
        ,,,,,,,
        (Pdb) pp args
        (1,uint256
        100,uint256
        1000,uint256
        b'arf',bytes32
        '0xc590dd7eed9f093d88d2f3c894b769c746bc8c9b',address
        66153838227408534191608590763201001504128600065912625980963590518282769258064,uint256
        0,uint8
        '{"template": "stable-diffusion", "params": ""}')string
        """
        txHash = self.ethclient.contract.functions.postJobOfferPartTwo(
            Web3.to_int(msg['ijoid']),
            # Web3.to_int(msg['ramLimit']),
            # Web3.to_int(msg['localStorageLimit']),
            "arf",
            Web3.to_checksum_address(msg['directory']),
            Web3.to_int(msg['hash']),
            Web3.to_int(0),
            jsonData,
        ).transact({
          "from": self.account,
        })

#         (1,
#  100,
#  1000,
#  1,
#  '0xc590dd7eed9f093d88d2f3c894b769c746bc8c9b',
#  66153838227408534191608590763201001504128600065912625980963590518282769258064,
#  'amd64',
#  '{"template": "stable-diffusion", "params": ""}')


        self.logger.info("D: postJobOfferPartTwo = %s" % (txHash,))

        return 0