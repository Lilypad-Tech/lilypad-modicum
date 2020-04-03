import logging
import logging.config
import os
import subprocess
import docker.errors
from . import DockerWrapper
from .PlatformClient import PlatformClient
from . import PlatformStructs as Pstruct
from . import helper
import dotenv
import time
import traceback
import json
import datetime



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
        tag,name = uri.split('_')
        urix = uri+"_"+str(ijoid)

        if self.sim:
            self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
            return 0 

        self.logger.info("L: Requesting Permission to get job = %s" %ijoid)
        msg = self.DC.getPermission(_DIRIP_, _DIRPORT_, self.account, tag, _KEY_)

        self.user = msg['user']
        self.groups = msg['groups']

        self.logger.info("L: permission granted? : %s = %s" %(msg['exitcode']==0, ijoid))

        if msg['exitcode'] != 0 :
            self.logger.info("Done.. but permission denied")
            statusJob=9
            endStatus="DirectoryUnavailable"
            self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
            return endStatus

        remote_user = self.DC.getUsername(_DIRIP_, _DIRPORT_, JID)
        
        # self.logger.info("Check job size")
        # result = self.DC.getSize(_DIRIP_, _SSHPORT_, self.user, remote_user, tag, _SSHKEY_)
        # self.logger.info("Job size is: \n %s" %result)
        # lines = result.split("\n")
        # for line in lines:
        #     self.logger.info(line)
        #     if "json" in line and "input" in line:
        #         inputSize = line.split("\t")[0]
        #         input_exists=True
        #     elif "tar" in line:
        #         imageSize = line.split("\t")[0]
        #         image_exits=True
        #         # size = line.split("\t")[0]
        #     elif "total" in line :
        #         size = line.split("\t")[0]
        #         self.logger.info("reported size: %s" %size)

        # if int(inputSize) > JO.localStorageLimit:
        #     statusJob = 5
        #     endStatus = "StorageExceeded"
        #     self.logger.info("input too big: %s %s>%s" %(endStatus,inputSize,JO.localStorageLimit))
        #     self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
        #     return endStatus


        # if int(imageSize) > JO.size:
        #     statusJob = 5
        #     endStatus = "StorageExceeded"
        #     self.logger.info("image too big: %s %s>%s" %(endStatus,imageSize,JO.size))
        #     self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
        #     return endStatus

        # if not image_exits:
        #     statusJob = 3
        #     endStatus = "JobNotFound"
        #     self.logger.info("Image does not exist")
        #     self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
        #     return endStatus

        # if not input_exists:
        #     statusJob = 3
        #     endStatus = "JobNotFound"
        #     self.logger.info("Input does not exist")
        #     self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
        #     return endStatus

        data = "*"

        self.logger.info([_DIRIP_,_SSHPORT_,self.user, JID, tag,_WORKPATH_ ,_SSHKEY_])
        localPath = "%s/%s/" %(_WORKPATH_, tag)
        # if os.path.isfile("%s/%s.tar" %(localPath,tag)):
        #     self.logger.info("image exists, skip downloading it.")
        #     localPath = "%s/input" %localPath
        #     data = "input.tar"
        os.makedirs(localPath, exist_ok=True) #HACK
        # self.logger.info("localPath: %s" %localPath)
        # self.logger.info("data: %s" %data)
        self.logger.info("K: get job = %s" %ijoid)
        self.DC.getData(host=_DIRIP_,sshport=_SSHPORT_,user=self.user,remote_user=remote_user,tag=tag,name=name,ijoid=ijoid,localPath=localPath,sshpath=_SSHKEY_)
        self.logger.info("K: got job = %s" %ijoid)

        try:
            if execute and statusJob==0:
                images = self.dockerClient.images.list(name=tag)

                if not images:
                    self.logger.info("Image not loaded. loading image... ")
                    images = DockerWrapper.loadImage(self.dockerClient, "%s/%s/%s.tar" %(_WORKPATH_, tag,tag))

                self.logger.info(images)
                self.logger.info("Image is loaded")
                jobHash_int = DockerWrapper.getImageHash(images[0])
                
                # if JO.hash != jobHash_int:
                #     statusJob = 2
                #     endStatus = "JobDescriptionError"
                #     self.logger.info("Image hash mismatch")
                #     self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
                #     return endStatus


                jobname = "%s_%s" %(tag, matchID)
                
                xdictPath = localPath+name+str(ijoid)+"/"+name+".json"
                self.logger.info("xdictPath: %s" %xdictPath)
                with open(xdictPath) as f:
                    xdict = json.load(f)

                self.logger.info("Starting Docker for job = %s" %ijoid)
                container = DockerWrapper.runContainer(self.dockerClient, tag, jobname, xdict)
                
                # container.reload()
                lid = container.attrs["Id"]
                self.logger.info("container ID for job %s: %s" %(lid, ijoid))

                self.logger.info("G: running job = %s" %ijoid)
                cpu_old = -1
                stopping = False
                cmd = "cat /sys/fs/cgroup/cpuacct/docker/%s/cpuacct.stat | grep -oP '(?<=user ).*'" %lid

                try:
                    self.logger.info("status: %s" %container.status)
                    while container.status != "running":
                        time.sleep(1)
                        container.reload()
                        self.logger.info(container.status)

                    while container.status == "running":
                        try:
                            completedprocess = subprocess.getoutput(cmd) #HACK the internet says something else should be used
                            cpuTime = int(completedprocess) * 10
                            if cpuTime > JO.instructionLimit:
                                statusJob = 6
                                endStatus = "InstructionsExceeded"
                                self.logger.info("Job exceeded alloted cpu time %s>%s" %(cpuTime,JO.instructionLimit))
                                self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
                                return endStatus

                        except ValueError as err:
                            self.logger.info("Process is done... probably")
                            self.logger.info("error is : %s" %err)
                            self.logger.info("error type is : %s" %type(err))
                            self.logger.info("G: %s to run job = %s" %(cpuTime, ijoid))
                            self.logger.info("Stopping Docker for job = %s" %ijoid)
                            stopping = True
                            # if lid in err:
                            #     self.logger.info("Process is done")

                        startReload = time.time()
                        container.reload()
                        reloadDuration = time.time() - startReload
                        self.logger.info("reload took: %s" %reloadDuration)
                        self.logger.info("Container is : %s" %container.status)
                        self.logger.info("duration: %s ms" %cpuTime)

                        if cpu_old == cpuTime or container.status != "running":
                            if not stopping:
                                self.logger.info("G: %s to run job = %s" %(cpuTime, ijoid))
                                self.logger.info("Stopping Docker for job = %s" %ijoid)
                                stopping = True
                        else:
                            cpu_old = cpuTime
                            time.sleep(1)
                except docker.errors.DockerException as err:
                    self.logger.info("Process was too fast to monitor")
                    self.logger.info("error is : %s" %err)
                    self.logger.info("error type is : %s" %type(err))


                self.logger.info("Docker stopped for job = %s" %ijoid)


                
                self.logger.info("Hash result for job = %s" %ijoid)
                
                output_filename = "%s/output.tar" %(localPath) #_WORKPATH_/tag/output.tar
                self.logger.info("output_filename = %s" %output_filename)
               
                output = next(iter(xdict['mounts']))
                self.logger.info("output directory = %s" %output)

                try :
                    helper.tar(output_filename,output)
                except FileNotFoundError: 
                    self.logger.warning("File does not exit = %s" %output)
                    os.makedirs(output, exist_ok=True) #HACK
                    helper.tar(output_filename,output)


                resultHash = helper.hashTar(output_filename)
                self.logger.info("outputTarHash = %s" %resultHash)

                self.logger.info("J: DC publishData = %s" %ijoid)
                
                self.DC.publishResult(host=_DIRIP_,port=_SSHPORT_,user=self.user,localpath=output,tag=tag,name=name,ijoid=ijoid,sshpath=_SSHKEY_)
                self.logger.info("J: DC dataPublished = %s" %ijoid)

                if self.account:
                    self.logger.info([matchID, endStatus, urix, resultHash, cpuTime, 0])
                    self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)

                self.logger.info("Done")
                return endStatus
        except :
            self.logger.info(traceback.format_exc())
            statusJob=8
            endStatus="ExceptionOccured"

        if statusJob!=0:
            if self.account:
                self.postResult(matchID, JO.offerId, endStatus, urix, resultHash, cpuTime, 0)
            return endStatus

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
        active = True
        while active:
            pass

    def platformListener(self):
        self.active = True
        while self.active:
            events = self.contract.poll_events()
            # self.logger.info("poll contract events")
            for event in events:
                params = event['params']
                name = event['name']
                transactionHash = event['transactionHash']

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
