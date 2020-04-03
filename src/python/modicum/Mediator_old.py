import logging
import logging.config
import os
import subprocess
from . import DockerWrapper
from .PlatformClient import PlatformClient
from . import PlatformStructs as Pstruct
import dotenv
import time
import traceback

class Mediator(PlatformClient):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("Mediator")
        # logging.config.fileConfig(os.path.dirname(__file__)+'/Modicum-log.conf')
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("---%(name)s---: \n%(message)s\n\r")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        self.job_offers = {}
        self.resource_offers = {}
        self.registered = False

        self.myMatches = {}

        path = dotenv.find_dotenv('.env', usecwd=True)
        dotenv.load_dotenv(path)

    def register(self, account, arch, instructionPrice, bandwidthPrice, dockerBandwidthPrice):
        self.logger.info("A: Registering")
        self.account = account
        self.contract.registerMediator(self.account, arch, instructionPrice, bandwidthPrice,  True, dockerBandwidthPrice)

    def getJob(self, tag, matchID, JID, execute, ijoid):
        _DIRIP_ = os.environ.get('DIRIP')
        _DIRPORT_ = os.environ.get('DIRPORT')
        _KEY_ = os.environ.get('pubkey')
        _SSHKEY_ = os.environ.get('sshkey')
        _SSHPORT_ = os.environ.get('SSHPORT')
        _WORKPATH_ = os.environ.get('WORKPATH')
        statusJob=0
        cpuTime=0
        endStatus="Completed"

        try :
            self.logger.info("L: Requesting Permission to get job")

            msg = self.DC.getPermission(msg["host"], msg["port"], msg["ijoid"], msg["job"], msg["pubkey"])

            self.user = msg['user']
            self.groups = msg['groups']
            self.logger.info("L: permission granted? : %s" % (msg['exitcode'] == 0))


            if msg['exitcode'] == 0:
                remote_user = self.DC.getUsername(_DIRIP_, _DIRPORT_, JID)

                self.logger.info("Check job size")
                result = self.DC.getSize(_DIRIP_, _SSHPORT_, self.user, remote_user, tag, _SSHKEY_)
                self.logger.info("Job size is: \n %s" %result)
                lines = result.split("\n")
                for line in lines:
                    self.logger.info(line)
                    if "json" in line and "input" in line:
                        input_exists=True
                    elif "tar" in line:
                        image_exits=True
                        # size = line.split("\t")[0]
                    elif "total" in line :
                        size = line.split("\t")[0]
                        self.logger.info(size)

                if image_exits :
                    if input_exists:
                        remotePath = tag
                        self.logger.info([_DIRIP_,_SSHPORT_,self.user, JID, tag,_WORKPATH_ ,_SSHKEY_])
                        localPath = "%s/%s/" %(_WORKPATH_, tag)
                        if os.path.isfile("%s/%s:latest.tar" %(localPath,tag)): #HACK
                            self.logger.info("image exists, skip downloading it.")
                            localPath = "%s/input" %localPath
                            remotePath = "%s/input" %tag
                        os.makedirs(localPath, exist_ok=True) #HACK
                        self.logger.info("localPath: %s" %localPath)
                        self.logger.info("remotePath: %s" %remotePath)
                        self.logger.info("K: get job = %s" %ijoid)
                        self.DC.getData(_DIRIP_,_SSHPORT_, self.user, remote_user, remotePath, localPath,_SSHKEY_)
                        self.logger.info("K: got job = %s" %ijoid)
                    else:
                        statusJob=3
                        endStatus="JobNotFound"
                        self.logger.info("Input does not exist")
                else:
                    statusJob=3
                    endStatus="JobNotFound"
                    self.logger.info("Image does not exist")
            else:
                self.logger.info("Done.. but permission denied")
                statusJob=9
                endStatus="DirectoryUnavailable"

        except :
            self.logger.info(traceback.format_exc())
            statusJob=3
            endStatus="JobNotFound"


        try:
            if execute and statusJob==0:
                images = self.dockerClient.images.list(name=tag)
                self.logger.info(images)

                if not images:
                    self.logger.info("Image not loaded. loading image... ")
                    DockerWrapper.loadImage(self.dockerClient, "%s/%s/%s:latest.tar" %(_WORKPATH_, tag,tag))

                self.logger.info("Image is loaded")

                jobname = "mm_%s" %matchID
                input = "%s/%s/input" %(_WORKPATH_,tag)
                output = "%s/%s/output" %(_WORKPATH_,tag)
                appinput = "/app/input"
                appoutput = "/app/output"
                self.logger.info("Starting Docker for job = %s" %ijoid)
                container = DockerWrapper.runContainer(self.dockerClient, tag, jobname, input, output,appinput,appoutput)
                # container.reload()
                lid = container.attrs["Id"]
                self.logger.info("container ID for job %s: %s" %(lid, ijoid))

                self.logger.info("G: running job = %s" %ijoid)
                cpu_old = -1
                stopping = False
                cmd = "cat /sys/fs/cgroup/cpuacct/docker/%s/cpuacct.stat | grep -oP '(?<=user ).*'" %lid

                self.logger.info(container.status)
                while container.status != "running":
                    time.sleep(1)
                    container.reload()
                    self.logger.info(container.status)
                while container.status == "running":
                    try:
                        completedprocess = subprocess.getoutput(cmd) #HACK the internet says something else should be used
                        cpuTime = int(completedprocess) * 10
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


                self.logger.info("Docker stopped for job = %s" %ijoid)
                # self.logger.info("J: Send result to DIRECTORY for job = %s" %ijoid)
                # self.DC.publishData(_DIRIP_, _SSHPORT_, self.user,tag,output,_SSHKEY_)
                # self.logger.info("J: Data sent for job = %s" %ijoid)

                if self.account:
                    #TODO resultHash
                    resultHash = "b599cff993a602c14e6d45beab7a48c25e6753b7106cd6173488e843a7158060"
                    resultHash_int = int(resultHash, 16)

                    # #TODO FAILURE HANDLING
                    self.logger.info("M: post mediation result: %s, RP at fault" %endStatus)

                    if self.myMatches[matchID]['resHash'] == resultHash_int:
                        pass
                        self.contract.postMediationResult(self.account,  True,
                            matchID, endStatus, tag, resultHash_int, cpuTime, 0, 0, 'CorrectResults', 'JobCreator')
                    else:
                        self.contract.postMediationResult(self.account,  True,
                                                          matchID, endStatus, tag, resultHash_int, cpuTime, 0, 0,
                                                          'WrongResults', 'ResourceProvider')

                self.logger.info("Done")
                return 0
        except :
            self.logger.info(traceback.format_exc())
            statusJob=8
            endStatus="ExceptionOccured"

        if statusJob!=0:
            if self.account:
                #TODO resultHash
                resultHash = "b599cff993a602c14e6d45beab7a48c25e6753b7106cd6173488e843a7158060"
                resultHash_int = int(resultHash, 16)

                # #TODO FAILURE HANDLING
                self.logger.info("M: Post Mediation result: %s, JC at fault" %endStatus)
                self.contract.postMediationResult(self.account,  True,
                    matchID, endStatus, tag, resultHash_int, cpuTime, 0, 0, 'InvalidResultStatus', 'JobCreator')


    def getJob_old(self, tag, matchID, JID, execute):
        _DIRIP_ = os.environ.get('DIRIP')
        _DIRPORT_ = os.environ.get('DIRPORT')
        _KEY_ = os.environ.get('pubkey')
        _SSHKEY_ = os.environ.get('sshkey')
        _SSHPORT_ = os.environ.get('SSHPORT')
        _WORKPATH_ = os.environ.get('WORKPATH')
        statusJob=0
        cpuTime=0
        endStatus="Completed"

        self.logger.info("Requesting Permission to get job")
        msg = self.DC.getPermission(_DIRIP_, _DIRPORT_,self.account,tag,_KEY_)
        self.user = msg['user']
        self.groups = msg['groups']
        self.logger.info("permission granted? : %s" %(msg['exitcode'] == 0))

        if msg['exitcode'] == 0:
            remotePath = tag
            self.logger.info([_DIRIP_,_SSHPORT_,self.user, JID, tag,_WORKPATH_ ,_SSHKEY_])
            localPath = "%s/%s/" %(_WORKPATH_, tag)
            if os.path.isfile("%s/%s:latest.tar" %(localPath,tag)): #HACK
                self.logger.info("image exists, skip downloading it.")
                localPath = "%s/input" %localPath
                remotePath = "%s/input" %tag
            os.makedirs(localPath, exist_ok=True) #HACK
            self.logger.info(localPath)
            self.logger.info("get job")
            self.DC.getData(_DIRIP_,_DIRPORT_,_SSHPORT_, self.user, JID, remotePath, localPath,_SSHKEY_)

            if execute:
                images = self.dockerClient.images.list(name=tag)
                self.logger.info(images)

                if not images:
                    self.logger.info("Image not loaded. loading image... ")
                    DockerWrapper.loadImage(self.dockerClient, "%s/%s/%s:latest.tar" %(_WORKPATH_, tag,tag))

                self.logger.info("Image is loaded")

                self.logger.info("running job")
                jobname = "mm_%s" %matchID
                input = "%s/%s/input" %(_WORKPATH_,tag)
                output = "%s/%s/output" %(_WORKPATH_,tag)
                appinput = "/app/input"
                appoutput = "/app/output"
                container = DockerWrapper.runContainer(self.dockerClient, tag, jobname, input, output,appinput,appoutput)
                container.reload()
                lid = container.attrs["Id"]
                self.logger.info("container ID: %s" %lid)

                while container.status == "running":
                    self.logger.info("Container is : %s" %container.status)

                    cmd = "cat /sys/fs/cgroup/cpuacct/docker/%s/cpuacct.stat | grep -oP '(?<=user ).*'" %lid
                    completedprocess = subprocess.getoutput(cmd) #HACK the internet says something else should be used
                    cpuTime = int(completedprocess) * 10
                    print("duration: %s ms" %cpuTime)

                    time.sleep(1)
                    container.reload()

                self.logger.info("Done running")
                self.logger.info("Send result to DIRECTORY")
                self.DC.publishData(_DIRIP_, _SSHPORT_, self.user,tag,output,_SSHKEY_)

                if self.account:
                    #TODO resultHash
                    resultHash = "b599cff993a602c14e6d45beab7a48c25e6753b7106cd6173488e843a7158060"
                    resultHash_int = int(resultHash, 16)

                    # #TODO FAILURE HANDLING
                    self.logger.info("M: post mediation result")

                    if self.myMatches[matchID]['resHash'] == resultHash_int:

                        self.contract.postMediationResult(self.account,  True,
                            matchID, 'Completed', tag, resultHash_int, cpuTime, 0, 0, 'CorrectResults', 'JobCreator')
                    else:
                        self.contract.postMediationResult(self.account,  True,
                                                          matchID, 'Completed', tag, resultHash_int, cpuTime, 0, 0,
                                                          'WrongResults', 'ResourceProvider')

                self.logger.info("Done")
                return 0
            else:
                return 0

        else:
            self.logger.info("Done.. but permission denied")
            return message

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

                if name == "MediatorRegistered" :
                    self.logger.info("A: %s" %name)
                elif name == "ResourceOfferPosted":
                    self.logger.info(name)
                    offer  = Pstruct.ResourceOffer(
                        params['offerId'], params['addr'],
                        params['instructionPrice'], params['instructionCap'],
                        params['memoryCap'], params['localStorageCap'],
                        params['bandwidthCap'], params['bandwidthPrice'],
                        params['dockerBandwidthCap'], params['dockerBandwidthPrice'], params['deposit'])
                    self.resource_offers[params['offerId']] =  offer

                elif name == "JobOfferPosted":
                    self.logger.info(name)
                    offer = Pstruct.JobOffer(
                        params['offerId'], params['jobCreator'], params['size'],
                        params['arch'], params['instructionLimit'], params['ramLimit'],
                        params['localStorageLimit'], params['bandwidthLimit'],
                        params['instructionMaxPrice'], params['bandwidthMaxPrice'],
                        params['dockerBandwidthMaxPrice'], params['completionDeadline'], params['deposit'])
                    self.job_offers[params['offerId']] = offer

                elif name == "Matched":
                    self.logger.info(name)
                    joid = params['jobOfferId']
                    roid = params['resourceOfferId']
                    mid = params['mediator']
                    matchID = params['matchId']

                    if mid == self.account:
                        self.myMatches[matchID] = {
                            'joid': joid,
                            'roid': roid
                        }
                        self.logger.info('I was matched: %s' % params['matchId'])

                elif name == "ResultPosted":
                    self.logger.info(name)
                    if params['matchId'] in self.myMatches:
                        self.myMatches[params['matchId']]['resHash'] = params['hash']

                elif name == "JobAssignedForMediation":
                    self.logger.info(name)
                    if params['matchId'] in self.myMatches:
                        matchID = params['matchId']
                        joid = self.myMatches[matchID]['joid']
                        JID = self.job_offers[joid].jobCreator
                        tag = self.job_offers[joid].uri
                        JID = JID = self.job_offers[joid].jobCreator
                        ijoid = self.job_offers[joid].ijoid

                        self.getJob(tag, matchID, JID, True, ijoid)

                elif name == "MediationResultPosted":
                    self.logger.info("M: %s" %name)

                elif name == "DebugString":
                    self.logger.info(params["str"])

            self.wait()
