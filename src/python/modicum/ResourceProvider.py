import logging
import logging.config
import subprocess
# from . import DirectoryClient
from . import DockerWrapper
from .PlatformClient import PlatformClient
from .Mediator import Mediator
from . import PlatformStructs as Pstruct
import time
import json
import traceback
import web3
from apscheduler.schedulers.background import BackgroundScheduler
from . import helper
import datetime
from .Enums import ResultStatus
import os

class ResourceProvider(Mediator):
    def __init__(self, index=0, sim=False):
        super().__init__(-1,sim)
        self.logger = logging.getLogger("ResourceProvider")
        # logging.config.fileConfig(os.path.dirname(__file__)+'/Modicum-log.conf')
        self.logger.setLevel(logging.INFO)
        
        # ch = logging.StreamHandler()
        # formatter = logging.Formatter("---%(name)s---:%(message)s")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.job_offers = {}
        self.resource_offers = {}
        self.matches ={}
        self.registered = False
        self.offerq = list()
        self.idle = True
        self.mediator = None
        self.index = index
        self.sim = sim

        self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "RP" + str(self.index)},
                       seriesname="state", value=1)

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def register(self, account, arch, timePerInstruction):
        self.logger.info("A: registerResourceProvider")
        self.account = account
        self.ethclient.transact(
            self.ethclient.contract.functions.registerResourceProvider(arch, timePerInstruction),
            { "from": self.account },
        )
        return 0

    def addMediator(self,account,mediator):
        self.logger.info("B: resourceProviderAddTrustedMediator")
        txHash = self.ethclient.transact(
            self.ethclient.contract.functions.resourceProviderAddTrustedMediator(mediator),
            { "from": self.account },
        )
        return 0

    def postOffer(self,msg):
        if self.idle:
            self.idle = False
            self.logger.info("C: postResOffer = %s" %msg["iroid"])
            self.logger.info("🟠 post resource offer")
            txHash = self.ethclient.transact(
                self.ethclient.contract.functions.postResOffer(
                    msg["instructionPrice"],
                    msg["instructionCap"],
                    msg["memoryCap"],
                    msg["localStorageCap"],
                    msg["bandwidthCap"],
                    msg["bandwidthPrice"],
                    msg["matchIncentive"],
                    msg["verificationCount"],
                    msg["iroid"]
                ),
                { "from": self.account, "value": msg["deposit"], },
            )
            return 0
        else:
            self.offerq.insert(0,msg)
            self.logger.info("RP is busy. Submit offer later")
            return 1

    def postDefaultOffer(self):
        deposit = self.ethclient.contract.functions.getRequiredResourceProviderDeposit().call()
        self.postOffer({"request": "post",
                        "deposit" : deposit,
                        "instructionPrice" : 0,
                        "bandwidthPrice" : 0,
                        "instructionCap" : 15*60*1000, #ms on 1Ghz processor
                        "memoryCap": 100000000,
                        "localStorageCap" : 1000000000,
                        "bandwidthCap" : 2**256-1,
                        
                        "matchIncentive" : 0,
                        "verificationCount" : 1,
                        "iroid" : round(time.time()*1000)
                        })

    def addSupportedFirstLayer(self, msg):
        self.logger.info('addSupportedFirstLayer n/a')

    def acceptResult(self, resultId):
        self.logger.info('JC Missed deadline for reacting to results.')
        txHash = self.ethclient.transact(
            self.contract.functions.acceptResult(resultId),
            { "from": self.account },
        )

    def scheduleAcceptResult(self, resultId, delay):
        to_run = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + delay))
        self.scheduler.add_job(self.acceptResult, 'date', id=str(resultId), run_date=to_run, args=[resultId])

    # we are using cpuTime as the way to actually price the job
    # the resource offer will have given us a cpu cost per instruction of 1
    # so we set the price by controlling the number of units
    def postResult(self, matchID, joid, resultHash):
        self.logger.info("🟢🟢🟢 Posting result: \n%s" % (json.dumps({
          "matchID": matchID,
          "joid": joid,
          "contractStatus": ResultStatus.Completed.value,
          "resultHash": resultHash,
        }),))
        self.ethclient.transact(
            self.ethclient.contract.functions.postResult(
                matchID,
                joid,
                ResultStatus.Completed.value,
                "",
                resultHash,
                0,
                0
            ),
            { "from": self.account },
        )


    def CLIListener(self):
        active = True
        while active:
            self.logger.info("Receiving...")
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
                self.logger.info("L: Requesting Permission to get job")
                msg = self.DC.getPermission(msg["host"],msg["port"],msg["ijoid"],msg["job"],msg["pubkey"])

                self.user = msg['user']
                self.logger.info("L: permission granted? : %s" %(msg['exitcode']==0))

                self.logger.info("J: DC publishData")
                self.DC.publishData(msg["host"],msg["sftport"],msg["ijoid"],msg["job"],msg["localpath"],msg["sshpath"])
                self.logger.info("J: DC dataPublished")
                self.cliSocket.send_pyobj("data published")
            elif msg['request'] == "post":
                exitcode = self.postOffer(msg)
                if exitcode == 0:
                    self.logger.info("resource offer posting")
                    self.cliSocket.send_pyobj("resource offer posting")
                elif exitcode == 1:
                    self.logger.info("resource offer queued")
                    self.cliSocket.send_pyobj("resource offer queued")

            elif msg['request'] == "getJob":
                exitcode = self.getJob(
                    msg['tag'],
                    msg['matchID'],
                    msg['JID'],
                    msg['execute'],
                    msg['ijoid']
                    )
                self.cliSocket.send_pyobj(exitcode)


    def platformListener(self):
        self.active = True
        self.logger.info(f"poll contract events on {self.ethclient.contract_address}")
        while self.active:
            events = self.ethclient.poll_events()
            for event in events:
                params = event['params']
                name = event['name']
                if name == "ResourceProviderRegistered" and self.account == params['addr']:
                # if name == "ResourceProviderRegistered":
                #     self.addr = params['addr']
                    self.logger.info("🔴 ResourceProviderRegistered: \n({}).".format(params))
                    self.penaltyRate = params['penaltyRate']
                    self.registered = True
                    self.logger.info("A: %s PenaltyRate : %s" %(name,self.penaltyRate))
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                elif name == "ResourceProviderAddedTrustedMediator" and self.account == params['addr']:
                    self.logger.info("🔴 ResourceProviderAddedTrustedMediator: \n({}).".format(params))
                    self.mediator = params['mediator']
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                    self.logger.info("B: %s" %name)
                elif name == "ResourceOfferPosted" and self.account == params['addr']:
                    self.logger.info("🔴 ResourceOfferPosted: \n({}).".format(params))
                    self.logger.info("C: %s = %s" %(name,params["iroid"]))
                    self.logger.info("OfferID: %s" %params['offerId'])

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

                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)

                elif "JobOfferPosted" in name: 
                    self.logger.info("🔴 JobOfferPosted: \n({}).".format(params))
                    self.logger.info("%s offerId = %s" %(name, params["offerId"]))
                    helper.storeJobOffer(event,self.job_offers)

                elif name == "Matched" and params['resourceOfferId'] in self.resource_offers:
                    self.logger.info("🔴 Matched: \n({}).".format(params))
                    joid = params['jobOfferId']
                    roid = params['resourceOfferId']
                    matchID = params["matchId"]
                    
                    self.logger.info("%s offerId= %s" % (name, matchID))
                    self.logger.info("Job offer %s = %s" % (name, self.job_offers[joid].ijoid))
                    self.logger.info("Resource offer %s = %s" % (name, self.resource_offers[roid].iroid))

                    match = Pstruct.Match(
                        joid, roid, params["mediator"]
                    )
                    self.matches[matchID] = match


                    JO = self.job_offers[joid]

                    # ijoid = JO.ijoid
                    # self.logger.info("%s Job = %s" %(name, ijoid))
                    # iroid = self.resource_offers[roid].iroid
                    # self.logger.info("%s Resource = %s" %(name, iroid))
                    # matchID = params["matchId"]
                    # uri = JO.uri
                    # self.logger.info("@@@  URI  @@@ %s" %uri)
                    # JID = JO.jobCreator

                    self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "RP" + str(self.index)},
                                          seriesname="state", value=2)

                    if os.environ.get('BAD_ACTOR') is not None:
                        self.logger.info("🔵🔵🔵 BAD ACTOR JOB")
                        resultHash = "muaahaaha"
                    else:
                        try:
                            resultHash = self.getJob(matchID, JO, True)
                        except Exception as e:
                            # TODO: pass this error state as more structured
                            # data through the rest of the system
                            resultHash = f"JOB_FAILED:{e} {e.output if hasattr(e, 'output') else ''}{e.stderr if hasattr(e, 'stderr') else ''}"
                            self.logger.info("🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨")
                            self.logger.info(f"JOB FAILED: {e} {e.output if hasattr(e, 'output') else ''}{e.stderr if hasattr(e, 'stderr') else ''}")
                            self.logger.info(traceback.format_exc())
                            self.logger.info("🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨")

                    self.postResult(matchID, JO.offerId, resultHash)

                    self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "RP" + str(self.index)},
                                          seriesname="state", value=1)

                    # once we have run a job let's post another offer
                    # TODO: remove this - it should be called as part of postOffer

                    # self.matches[matchID] = {"uri":uri,"JID":JID,"execute":True}

                elif name == "ResultPosted" and params["matchId"] in self.matches:
                    self.logger.info("🔴 ResultPosted: \n({}).".format(params))
                    self.logger.info("H: %s" %name)
                    self.logger.info("result posted for matchId : %s" %params["matchId"])
                    self.logger.info("resultID for matchId : %s" % params["resultId"])

                    matchID = params["matchId"]
                    joid = self.matches[matchID].jobOfferId

                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=-1)

                    # self.matches[params['matchId']]['resultId'] = params['resultId']
                    # self.scheduleAcceptResult(params['resultId'], 1440)
                    self.idle = True
                    self.postDefaultOffer()

                elif name == "ResultReaction" and params["matchId"] in self.matches:
                    self.logger.info("🔴 ResultReaction: \n({}).".format(params))
                    self.logger.info("%s" % name)
                    self.logger.info("%s" % params)
                    self.logger.info("result ResultReaction for matchId : %s" % params["matchId"])

                    matchID = params["matchId"]

                    self.logger.info("show matches: %s" % (self.matches))
                    self.logger.info("matchID: %s" %matchID)

                    roid = self.matches[matchID].resourceOfferId
                    iroid = self.resource_offers[roid].iroid

                    self.logger.info("F: %s = %s" %(name, iroid))

                    joid = self.matches[matchID].jobOfferId
                    ijoid = self.job_offers[joid].ijoid

                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid)

                    # self.scheduler.remove_job(str(params['resultId']))

                elif name == "MatchClosed" and params["matchId"] in self.matches:
                    self.logger.info("🔴 MatchClosed: \n({}).".format(params))
                    matchID = params["matchId"]
                    joid = self.matches[matchID].jobOfferId
                    ijoid = self.job_offers[joid].ijoid
                    roid = self.matches[matchID].resourceOfferId
                    iroid = self.resource_offers[roid].iroid


                    self.logger.info("Q: %s matchID = %s" % (name, matchID))
                    self.logger.info("Q: %s Job = %s" %(name, ijoid))
                    self.logger.info("Q: %s Resource = %s" %(name, iroid))

                    self.logger.info("%s" % name)
                    

                elif name == "DebugString":
                    self.logger.info(params["str"])

                elif name == "EtherTransferred":
                    self.logger.info("🟡 EtherTransferred: \n({}).".format(params))

            if self.idle and self.offerq:
                offer = self.offerq.pop()
                self.postOffer(offer)

            self.wait()
