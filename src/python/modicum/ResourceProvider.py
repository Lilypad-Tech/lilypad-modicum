import logging
import logging.config
import subprocess
# from . import DirectoryClient
from . import DockerWrapper
from .PlatformClient import PlatformClient
from .Mediator import Mediator
from . import PlatformStructs as Pstruct
import time
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from . import helper
import datetime

class ResourceProvider(Mediator):
    def __init__(self, index,sim):
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
        txHash = self.contract.registerResourceProvider(account, True, arch, timePerInstruction)
        # helper.wait4receipt(self.ethclient,txHash)
        return 0

    def addMediator(self,account,mediator):
        self.logger.info("B: resourceProviderAddTrustedMediator")
        txHash = self.contract.resourceProviderAddTrustedMediator(account, True, mediator)
        # helper.wait4receipt(self.ethclient,txHash)
        return 0

    def postOffer(self,msg):
        if self.idle:
            self.idle = False
            self.logger.info("C: postResOffer = %s" %msg["iroid"])
            txHash = self.contract.postResOffer(self.account, True,
                            msg["deposit"],
                            msg["instructionPrice"],
                            msg["instructionCap"],
                            msg["memoryCap"],
                            msg["localStorageCap"],
                            msg["bandwidthCap"],
                            msg["bandwidthPrice"],
                            msg["matchIncentive"],
                            msg["verificationCount"],
                            msg["iroid"]
                            )
            # helper.wait4receipt(self.ethclient,txHash)
            return 0
        else:
            self.offerq.insert(0,msg)
            self.logger.info("RP is busy. Submit offer later")
            return 1

    def addSupportedFirstLayer(self, msg):
        self.contract.resourceProviderAddSupportedFirstLayer(
            self.account,
            msg['firstLayerHash']
        )

    def acceptResult(self, resultId):
        self.logger.info('JC Missed deadline for reacting to results.')
        self.contract.acceptResult(self.account, True, resultId)

    def scheduleAcceptResult(self, resultId, delay):
        to_run = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + delay))
        self.scheduler.add_job(self.acceptResult, 'date', id=str(resultId), run_date=to_run, args=[resultId])


    # # IS THIS EVER CALLED? OR JUST THE MEDIATOR ONE?
    # THE RP post result is different. postResult vs postMediationResult
    def postResult(self, matchID, joid, endStatus, uri, resultHash, cpuTime, bandwidthUsage):
        resultHash_int = int(resultHash, 16)
        self.logger.info("H: postResult = %s" %uri)
        self.contract.postResult(self.account, True, matchID, joid, endStatus, uri,
                                 resultHash_int, cpuTime, bandwidthUsage)


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
        while self.active:
            events = self.contract.poll_events()
            # self.logger.info("poll contract events")
            for event in events:
                params = event['params']
                name = event['name']
                # self.logger.info("{}({}).".format(name, params))
                if name == "ResourceProviderRegistered" and self.account == params['addr']:
                # if name == "ResourceProviderRegistered":
                #     self.addr = params['addr']
                    self.penaltyRate = params['penaltyRate']
                    self.registered =True
                    self.logger.info("A: %s PenaltyRate : %s" %(name,self.penaltyRate))
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                elif name == "ResourceProviderAddedTrustedMediator" and self.account == params['addr']:
                    self.mediator = params['mediator']
                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=-1, ijoid=-1)
                    self.logger.info("B: %s" %name)
                elif name == "ResourceOfferPosted" and self.account == params['addr']:
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
                    self.logger.info("%s offerId = %s" %(name, params["offerId"]))
                    helper.storeJobOffer(event,self.job_offers)

                elif name == "Matched" and params['resourceOfferId'] in self.resource_offers:
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
                    ResultStatus = self.getJob(matchID, JO, True)
                    self.helper.logInflux(now=datetime.datetime.now(), tag_dict={"object": "RP" + str(self.index)},
                                          seriesname="state", value=1)

                    # self.matches[matchID] = {"uri":uri,"JID":JID,"execute":True}

                elif name == "ResultPosted" and params["matchId"] in self.matches:
                    self.logger.info("H: %s" %name)
                    self.logger.info("result posted for matchId : %s" %params["matchId"])
                    self.logger.info("resultID for matchId : %s" % params["resultId"])

                    matchID = params["matchId"]
                    joid = self.matches[matchID].jobOfferId

                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=-1)

                    # self.matches[params['matchId']]['resultId'] = params['resultId']
                    # self.scheduleAcceptResult(params['resultId'], 1440)
                    self.idle = True

                elif name == "ResultReaction" and params["matchId"] in self.matches:

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

            if self.idle and self.offerq:
                offer = self.offerq.pop()
                self.postOffer(offer)

            self.wait()
