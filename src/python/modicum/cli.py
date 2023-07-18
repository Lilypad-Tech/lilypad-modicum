import click
import os
import sys
import time
import zmq
import logging
import json
from web3 import Web3
from .JobCreator import JobFinished
import subprocess
import shlex
from .Enums import Architecture
from .Modules import get_bacalhau_job_arch
from halo import Halo

# logFormatter = logging.Formatter('%(levelname)s - %(threadName)s - %(asctime)s - %(name)s - %(message)s')
logFormatter = logging.Formatter('%(asctime)s;%(name)s;%(message)s')
rootLogger = logging.getLogger()


fileHandler = logging.FileHandler("{0}/{1}.log".format(os.getenv("HOME"), 'modicum'))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

logging.getLogger('fabric')

# sys.stdout = LoggerWriter.LoggerWriter(rootLogger.info)
# sys.stderr = LoggerWriter.LoggerWriter(rootLogger.warning)
# mediator = '0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266'
# mediator = '0x21822993d2a654e90d4f8f837a8af8a2e23c686f'


try:
    import dotenv
except ImportError:
    dotenv = None

from modicum import config as cfg
from modicum import DockerWrapper as DW
from modicum import helper

@click.command('foo')
# @main.command('foo')
@click.option('--count', required=False, default=1, help='number of greetings', show_default=True)
@click.argument('name', default="John Doe")
def foo_command(count, name):
    for x in range(count):
        click.echo('Hello %s!' % name)


def num_system_GPUs():
    nvidia_cli = "nvidia-container-cli"

    try:
        nvidia_path = subprocess.check_output(shlex.split(f"which {nvidia_cli}")).decode().strip()
    except subprocess.CalledProcessError:
        # If the NVIDIA CLI is not installed, we can't know the number of GPUs, assume zero
        return 0

    args = ["info", "--csv"]
    cmd = [nvidia_path] + args

    try:
        resp = subprocess.check_output(cmd).decode()
    except subprocess.CalledProcessError as e:
        print(e)
        return 0

    # Parse output of nvidia-container-cli command
    lines = resp.split("\n")
    device_info_flag = False
    num_devices = 0
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        if line.startswith("Device Index"):
            device_info_flag = True
            continue
        if device_info_flag:
            num_devices += 1

    print(num_devices)
    return num_devices

def get_arch():
    numGPU = num_system_GPUs()
    arch = Architecture.cpu.value
    if numGPU > 0:
        arch = Architecture.gpu.value
    return arch

ctxt = zmq.Context()
################################################################################
# interact
################################################################################
@click.command('interact')
def interact():
    import code
    code.interact()

################################################################################
# DIRECTORY CLI
################################################################################
@click.command('runAsDir')
def runAsDir():
    from modicum import Directory as Directory
    _DIRPORT_ = os.environ.get('DIRPORT')
    _DIRCHILDPORT_ = os.environ.get('DIRCHILDPORT')

    D = Directory.Directory()
    D.startServer(port=_DIRPORT_,childport=_DIRCHILDPORT_)

@click.command('stopDir')
def stopDir():
    _DIRIP_ = os.environ.get('DIRIP')
    _DIRPORT_ = os.environ.get('DIRPORT')
    _DIRCHILDPORT_ = os.environ.get('DIRCHILDPORT')

    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %(_DIRIP_,_DIRPORT_))

    msg = {"request": "stop"}
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

################################################################################
# SOLVER CLI
################################################################################
@click.command('runAsSolver')
@click.option('--index', default=0, show_default=True)
def runAsSolver(index):
    from modicum import Solver as Solver
    _CONTRACT_ADDRESS_ = os.environ.get('CONTRACT_ADDRESS')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    S = Solver.Solver(index)

    S.startCLIListener(7654)

    S.platformConnect(_CONTRACT_ADDRESS_, _GETHIP_,_GETHPORT_,index)

@click.command('stopSolver')
def stopSolver():
    eventSender = ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',7654))
    msg = {"request": "stop"}
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

################################################################################
# MEDIATOR CLI
################################################################################
@click.command('runAsMediator')
@click.option('--index', default=0, show_default=True)
@click.option('--sim')
def runAsMediator(index,sim):
    from modicum import Mediator as Mediator
    _CONTRACT_ADDRESS_ = os.environ.get('CONTRACT_ADDRESS')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    M = Mediator.Mediator(index,sim=="True")

    M.startCLIListener(8765)

    M.platformConnect(_CONTRACT_ADDRESS_, _GETHIP_, _GETHPORT_, index)

    # exitcode = M.test(1)

    click.echo("Mediator is registering... %s" % (M.account,))
    M.register(M.account, get_arch(), instructionPrice=1,
               bandwidthPrice=1,availabilityValue=1, verificationCount=1)

    while not M.registered:
        time.sleep(0.1)
    click.echo("Mediator has registered")


@click.command('stopMediator')
def stopMediator():
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',8765))
    msg = {"request": "stop"}
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)


################################################################################
# JC CLI
################################################################################

@click.command('startJC')
@click.option('-p','--playerpath')
@click.option('--index', default=0, show_default=True)
@click.option('-h', '--host',default=None)
@click.option('--sim')
def startJC(playerpath,index,host,sim):
    from modicum import JobCreator

    if host:
        _CONTRACT_ADDRESS_ = host
        _GETHIP_ = host
        _GETHPORT_ = os.environ.get('GETHPORT')
    else:
        _CONTRACT_ADDRESS_ = os.environ.get('CONTRACT_ADDRESS')
        _GETHIP_ = os.environ.get('GETHIP')
        _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CONTRACT_ADDRESS_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    # print(playerpath)
    # print(index)

    JC = JobCreator.JobCreator(index,sim=="True")
    JC.startCLIListener(cliport=7777)
    JC.platformConnect(_CONTRACT_ADDRESS_, _GETHIP_, _GETHPORT_,index)
    click.echo("Job Creator Daemon is registering... ")
    JC.register(JC.account)
    while not JC.registered:
        time.sleep(0.1)
    # click.echo("JC has registered")

    # mediator = '0x067d6f1ee89b6ccc4a057a19f2071dcdfb42e40c'
    exitcode = JC.addMediator(JC.account, mediator)
    while not JC.mediator:
        time.sleep(0.1)

    if sim =="True":  
        # postOffer /home/riaps/projects/MODiCuM/workloads/stress-ng/job stress-ng run 2 False END      
        path = "/home/riaps/projects/MODiCuM/workloads/stress-ng/job"
        tag = "stress-ng"
        name = "run"
        reject = "False"
        desc_path = "%s/%s/description.json" %(path,name)
        with open(desc_path, "r") as infile:
            sim_description = json.load(infile)        
        for i in range(100):
            '''0 to n-1, range(n)'''
            if JC.jobsPending >= 100:
                while JC.jobsPending > 0:
                    time.sleep(5)
            
            description = sim_description
            description["ijoid"] = i+1
            description["uri"] = "%s_%s" %(tag,name)
            description["reject"] = reject
            completionDeadline = int(round((time.time()+15*60)*1000)) #in ms
            description["completionDeadline"] = completionDeadline
                
            exitcode = JC.postOffer(description,getReceipt=False)
        
    else:
        with open(playerpath+"player"+str(index), 'r') as f:
            lines = f.readlines()
            for line in lines:
                print(line)
                call, path, tag, name, ijid, reject, END = line.split(" ")
                
                if call == "publish":
                    print("publish")
                    
                    exitcode = JC.publish(path,tag,name,ijid)
                
                elif call == "postOffer":
                    desc_path = "%s/%s/description.json" %(path,name)
                    with open(desc_path, "r") as infile:
                        description = json.load(infile)
                    
                    description["ijoid"] = int(ijid)
                    description["uri"] = "%s_%s" %(tag,name)
                    description["reject"] = reject
                    
                    completionDeadline = int(round((time.time()+15*60)*1000)) #in ms
                    description["completionDeadline"] = completionDeadline
                    
                    exitcode = JC.postOffer(description,getReceipt=True)


                else:
                    pass

@click.command('startJCDaemon')
@click.option('--index', default=0, show_default=True)
def startJCDaemon(index):
    from modicum import JobCreator
    _CONTRACT_ADDRESS_ = os.environ.get('CONTRACT_ADDRESS')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CONTRACT_ADDRESS_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    JC = JobCreator.JobCreator()
    JC.startCLIListener(cliport=7777)
    JC.platformConnect(_CONTRACT_ADDRESS_, _GETHIP_, _GETHPORT_,index)
    print("Job Creator Daemon is registering... ")
    exitcode = JC.register(JC.account)
    print("exitcode: %s" %exitcode)
    while not JC.registered:
        time.sleep(0.1)
    print("JC has registered")

    # mediator = '0x067d6f1ee89b6ccc4a057a19f2071dcdfb42e40c'
    print("Job adding mediator... ")
    exitcode = JC.addMediator(JC.account, mediator)
    while not JC.mediator:
        time.sleep(0.1)
    

@click.command('stopJCDaemon')
def stopJCDaemon():
    #TODO These should have a timeout
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',7777))
    msg = {"request": "stop"}
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

@click.command('JCaddMediator')
def JCaddMediator():
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',7777))
    msg = {"request": "addMediator",
           "mediator": mediator}


    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

@click.command('publishJob')
@click.option('-p', '--path', required=True, envvar='JOBPATH')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
@click.option('-n', '--name')
def publishJob(path,tag,name):
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',7777))
    msg = {"request": "publish",
           "path": path,
           "tag" : tag,           
           "name" : name
           }
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

@click.command('postJob')
@click.option('-p', '--path', required=True)
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
@click.option('-n', '--name',  required=True, envvar="JOBNAME")
@click.option('--myoid', default=1, show_default=True)
def postJob(path,tag,name,myoid):
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',7777))

    with open(path, "r") as infile:
        description = json.load(infile)
    
    description["request"] = "post"

    description["ijoid"] = myoid    
    description["uri"] = "%s_%s" %(tag,name)
        
    completionDeadline = int(round((time.time()+15*60)*1000)) #in ms
    description["completionDeadline"] = completionDeadline

    eventSender.send_pyobj(description)
    response = eventSender.recv_pyobj()
    click.echo(response)



@click.command()
@click.option('-p', '--path', required=True, envvar='JOBPATH')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
@click.option('--tar', required=True, default=False)
@click.option('-s', '--skip_build', is_flag=True)
def build(path, tag, tar, skip_build):
    client = DW.getDockerClient()

    if skip_build:
        click.echo("skip build = %s" %skip_build)
        image = client.images.get("%s:latest" %tag)
        click.echo(image)
    else:
        click.echo("building image...")
        image = DW.buildImage(client,path,tag)


    jobHash_int = DW.getImageHash(image)
    click.echo(jobHash_int)

    if tar:
        tag = image.tags[0]
        click.echo("tarring %s... " %tag)
        image_tarPath = "%s/image/%s.tar" %(path,tag)
        tarHash = DW.saveImage(path+"/image/", tag+".tar", image)

        tarHash = helper.hashTar(image_tarPath)
        tarHash_int = int(tarHash, 16)

        job_size = os.path.getsize(image_tarPath)
        click.echo("job_size: %s" %job_size)

        description_path = "%s/image/build.json" %(path)
        with open(description_path, "w+") as outfile:
            description = { "deposit" : -1, #Not set during build
                            "jobHash_int" :  jobHash_int,
                            "uri" : tag,
                            "size" : job_size, #size of the docker image
                            "arch" : "cpu",
                            "cpuTime" : -1, #Not set during build
                            "LocalStorageLimit" :  -1 , #Not set during build
                            "instructionMaxPrice" : 1,
                            "bandwidthMaxPrice" : -1, #Not set during build
                            "completionDeadline" : -1,#Not set during build
                             }
            json.dump(description, outfile)
    

@click.command()
@click.option('-p', '--path', required=True, envvar='JOBPATH')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
@click.option('-n', '--name',  required=True, envvar="JOBNAME")
def run(path, tag, name):
    client = DW.getDockerClient()
    
    with open(path+name+".json", "r") as f:
        xdict = json.load(f)

    container = DW.runContainer(client,tag, name, xdict)

@click.command()
@click.option('-p', '--path', required=True, envvar='JOBPATH')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
@click.option('-n', '--name',  required=True, envvar="JOBNAME")
def profile(path, tag, name):
    #path = MODiCuM/workloads/stress-ng/job
    #tag = stress-ng
    #name = run1
    client = DW.getDockerClient()

    image = client.get(tag)
    jobHash_int = DW.getImageHash(image)

    container = DW.runContainer(client,tag, name, xdict)
    userCPU, meanMEM = helper.profiler(path,tag,name, container)

    description = { "deposit":-1, #set during postJob
                    "ijoid":-1, #set during postJob
                    "cpuTime": int(userCPU * 1.1),
                    "bandwidthLimit":-1,
                    "instructionMaxPrice":1,
                    "bandwidthMaxPrice":1,
                    "completionDeadline":-1, #set during postJob
                    "matchIncentive":10,
                    "firstLayerHash":jobHash_int,
                    "ramLimit":2*meanMEM,
                    "localStorageLimit":-1,
                    "uri":-1,
                    "directory":-1,
                    "hash":-1,
                    "arch":"cpu"}


@click.command('getResult')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
@click.option('--rid', required=True, envvar="RID")
def getResult(tag,rid):
    # ------HACK for testing primarily------------
    from modicum import DirectoryClient
    _DIRIP_ = os.environ.get('DIRIP')
    _DIRPORT_ = os.environ.get('DIRPORT')
    _ID_ = os.environ.get('JID') #must be less than 32 characters and start with a letter
    _KEY_ = os.environ.get('pubkey')

    DC = DirectoryClient.DirectoryClient()
    click.echo("Requesting Permission")
    message, username = DC.getPermission(_DIRIP_,_DIRPORT_,_ID_,tag,_KEY_)

    click.echo(message)
    click.echo("permission granted? : %s" %(message==0))
    if message == 0:
    #-------END HACK --------------------------------------

        eventSender =ctxt.socket(zmq.REQ)
        eventSender.connect("tcp://%s:%s" %('localhost',7777))
        msg = {"request": "getResult",
               "user": username,
               "tag" : tag,
               "resultID" : 1,
               "RID" : rid
               }
        eventSender.send_pyobj(msg)
        response = eventSender.recv_pyobj()
        click.echo(response)

@click.command('getSize')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
def getSize(tag):
    from modicum import DirectoryClient
    _DIRIP_ = os.environ.get('DIRIP')
    _DIRPORT_ = os.environ.get('DIRPORT')
    _ID_ = os.environ.get('JID')
    _KEY_ = os.environ.get('pubkey')
    _SSHKEY_ = os.environ.get('sshkey')
    _SSHPORT_ = os.environ.get('SSHPORT')

    DC = DirectoryClient.DirectoryClient()
    message, username = DC.getPermission(_DIRIP_,_DIRPORT_,_ID_,tag,_KEY_)
    click.echo("permission granted? : %s" %(message==0))
    print(username)

    size = DC.getSize(_DIRIP_, _SSHPORT_, username, tag, _SSHKEY_)
    print(size)


################################################################################
# RP CLI
################################################################################
@click.command('startRP')
@click.option('-p','--path')
@click.option('--index', default=0, show_default=True)
@click.option('-h','--host',default=None)
@click.option('--sim')
@click.option('--mediator', default=None, show_default=True)
def startRP(path,index,host,sim,mediator):
    from modicum import ResourceProvider

    if host:
        _CONTRACT_ADDRESS_ = host
        _GETHIP_ = host
        _GETHPORT_ = os.environ.get('GETHPORT')
    else:
        _CONTRACT_ADDRESS_ = os.environ.get('CONTRACT_ADDRESS')
        _GETHIP_ = os.environ.get('GETHIP')
        _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CONTRACT_ADDRESS_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    RP = ResourceProvider.ResourceProvider(index,sim=="True")
    RP.startCLIListener(cliport=9999)
    print("CLI is listening...")

    # NOTE: we force index index here so we are only ever using either
    # the first (unlocked) account or the overriden account supplied by the env
    RP.platformConnect(_CONTRACT_ADDRESS_, _GETHIP_, _GETHPORT_, 0)
    print("Resource Provider Daemon is registering... ")
    exitcode = RP.register(RP.account,get_arch(), 1)# ratio to 1Gz processor # XXX should this be arm64???
    print("exitcode:  %s" %exitcode)
    while not RP.registered:
        time.sleep(0.1)
    print("RP has registered")

    if mediator is None and os.environ.get('MEDIATOR_ADDRESSES') is not None and os.environ.get('MEDIATOR_ADDRESSES') != "":
        mediator = os.environ.get('MEDIATOR_ADDRESSES').split(',')[0]

    if mediator is None or mediator == "":
        raise Exception("No mediator specified in comma seperated MEDIATOR_ADDRESSES environment variable")


    mediator = Web3.to_checksum_address(mediator)

    print("Resource Provider adding mediator... ")
    exitcode = RP.addMediator(RP.account, mediator)

    while not RP.mediator:
        time.sleep(0.1)

    while not RP.idle:
        time.sleep(0.1)

    exitcode = RP.postDefaultOffer()

@click.command('startRPDaemon')
@click.option('--index', default=0, show_default=True)
def startRPDaemon(index):
    from modicum import ResourceProvider
    _CONTRACT_ADDRESS_ = os.environ.get('CONTRACT_ADDRESS')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CONTRACT_ADDRESS_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    RP = ResourceProvider.ResourceProvider()
    RP.startCLIListener(cliport=9999)
    print("CLI is listening...")

    RP.platformConnect(_CONTRACT_ADDRESS_, _GETHIP_, _GETHPORT_,index)
    print("Resource Provider Daemon is registering... ")
    exitcode = RP.register(RP.account,get_arch(), 1)# ratio to 1Gz processor
    print("exitcode:  %s" %exitcode)
    while not RP.registered:
        time.sleep(0.1)
    print("RP has registered")


    # mediator = '0x067d6f1ee89b6ccc4a057a19f2071dcdfb42e40c'
    print("Resource Provider adding mediator... ")
    exitcode = RP.addMediator(RP.account, mediator)
    while not RP.mediator:
        time.sleep(0.1)


@click.command('stopRPDaemon')
def stopRPDaemon():
    #TODO These should have a timeout
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',9999))
    msg = {"request": "stop"}
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

@click.command('RPaddMediator')
def RPaddMediator():
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',9999))
    msg = {"request": "addMediator",
           "mediator": mediator}
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

@click.command('RPpostOffer')
@click.option('--myoid', default=1, show_default=True)
def RPpostOffer(myoid):
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',9999))
    msg = {"request": "post",
           "deposit" : 1000,
           "instructionPrice" : 1,
           "instructionCap" : 15*60*1000, #ms on 1Ghz processor
           "memoryCap": 100000000,
           "localStorageCap" : 1000000000,
           "bandwidthCap" : 2**256-1,
           "bandwidthPrice" : 1,
           "matchIncentive" : 1,
           "verificationCount" : 1,
           "iroid" : myoid
           }

    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)

@click.command('getJob')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
@click.option('--jid', required=True, envvar="JID")
def getJob(tag,jid):
    eventSender =ctxt.socket(zmq.REQ)
    eventSender.connect("tcp://%s:%s" %('localhost',9999))
    msg = {"request": "getJob",
           "tag" : tag,
           "matchID" : 1,
           "JID" : jid,
           "execute" : True
           }
    eventSender.send_pyobj(msg)
    response = eventSender.recv_pyobj()
    click.echo(response)


@click.command('loadImage')
@click.option('-p', '--path', required=True, envvar='WORKPATH')
@click.option('-t', '--tag',  required=True, envvar="JOBTAG")
def loadImage(path,tag):
    client = DW.getDockerClient()
    images = DW.loadImage(client, "%s/%s/%s:latest.tar" %(path, tag,tag))
    click.echo(images)




################################################################################
# MAIN
################################################################################

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if dotenv is None:
        if os.path.isfile('.env') or os.path.isfile('.flaskenv'):
            click.secho(
                ' * Tip: There are .env or .flaskenv files present.'
                ' Do "pip install python-dotenv" to use them.',
                fg='yellow')
        return

    path = dotenv.find_dotenv('.env', usecwd=True)
    dotenv.load_dotenv(path)

    if ctx.invoked_subcommand is None:
        click.echo('I was invoked without subcommand')


# TODO: new runLilypadCLI subcommand for 'lilypad' cli to exec into.
@click.command('runLilypadCLI')
@click.option('--template', default="stable_diffusion", show_default=True)
@click.option('--params', default="", show_default=True)
@click.option('--mediator', default=None, show_default=True)
def runLilypadCLI(template, params, mediator):
    from modicum import JobCreator
    _CONTRACT_ADDRESS_ = os.environ.get('CONTRACT_ADDRESS')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')
    
    index = 0
    JC = JobCreator.JobCreator(index, False)
    
    # User facing, quiet logging
    import logging
    logger = logging.getLogger("JobCreator")
    logger.setLevel(logging.ERROR)
    logger = logging.getLogger("EthereumClient")
    logger.setLevel(logging.ERROR)

    print(f"\n🌟 Lilypad submitting job {template}({params}) 🌟\n")

    spinner = Halo(text='Connecting to smart contract', spinner='pong')
    spinner.start()
    JC.platformConnect(_CONTRACT_ADDRESS_, _GETHIP_, _GETHPORT_, index)
    spinner.stop_and_persist("🔗")

    if os.environ.get('PRIVATE_KEY') is not None:
        print(f"🔑 Loaded private key for {JC.account}")
    
    spinner = Halo(text='Registering job creator', spinner='pong')
    spinner.start()
    JC.register(JC.account)
    while not JC.registered:
        time.sleep(0.1)
    spinner.stop_and_persist("🔌")

    if mediator is None and os.environ.get('MEDIATOR_ADDRESSES') is not None and os.environ.get('MEDIATOR_ADDRESSES') != "":
        mediator = os.environ.get('MEDIATOR_ADDRESSES').split(',')[0]

    if mediator is None or mediator == "":
        raise Exception("No mediator specified in comma seperated MEDIATOR_ADDRESSES environment variable")

    mediator = Web3.to_checksum_address(mediator)

    spinner = Halo(text=f'Adding mediator {mediator}', spinner='pong')
    spinner.start()
    exitcode = JC.addMediator(JC.account, mediator)
    while not JC.mediator:
        time.sleep(0.1)
    spinner.stop_and_persist("🧘")
    
    lastSpinner = "Posting"
    spinner = Halo(text=f'Posting offer for {template}', spinner='pong')
    spinner.start()
    exitcode = JC.postLilypadOffer(template, params)

    # Threading is terrible. Poll a freaking shared variable.
    lastState = JC.state

    statemojis = {
        "JobOfferPostedTwo": "💼",
        "Matched": "🥰",
        "Posting": "💌",
        "ResultsPosted": "💌",
    }
    descriptions = {
        "JobOfferPostedTwo": "Scheduling on-chain...",
        "Matched": "Running job...",
        "Posting": "Fetching results (posting)...",
        "ResultsPosted": "Fetching results...",
    }
    while not JC.finished:
        if JC.state != lastState:
            spinner.stop_and_persist(statemojis.get(lastSpinner, lastSpinner))
            lastSpinner = JC.state
            spinner = Halo(text=f'{descriptions.get(JC.state, JC.state)} {JC.status}', spinner='pong')
            spinner.start()
            lastState = JC.state
        
        # print(f"STATUS --> {JC.state} {JC.status}")
        time.sleep(0.01)

    spinner.stop_and_persist("🍃")

    print(f"\n🍂 Lilypad job completed 👉 {JC.status}\n")

    os._exit(0)



main.add_command(foo_command)
main.add_command(build)
main.add_command(run)
main.add_command(runAsDir)
main.add_command(stopDir)
main.add_command(runAsSolver)
main.add_command(stopSolver)
main.add_command(runAsMediator)
main.add_command(stopMediator)
main.add_command(startJC)
main.add_command(startJCDaemon)
main.add_command(stopJCDaemon)
main.add_command(JCaddMediator)
main.add_command(publishJob)
main.add_command(postJob)
main.add_command(startRP)
main.add_command(startRPDaemon)
main.add_command(stopRPDaemon)
main.add_command(RPaddMediator)
main.add_command(RPpostOffer)
main.add_command(getJob)
main.add_command(loadImage)
main.add_command(getResult)
main.add_command(getSize)
main.add_command(runLilypadCLI)

# main.add_command(profile)
