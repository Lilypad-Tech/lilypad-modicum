import click
import os
import sys
import time
import influxdb
import zmq
import tarfile
import hashlib
import logging
import json
import math
from . import LoggerWriter

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

mediator = '0x21822993d2a654e90d4f8f837a8af8a2e23c686f'


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


ctxt = zmq.Context()
################################################################################
# interact
################################################################################
@click.command('interact')
def interact():
    import code
    code.interact()

################################################################################
# EthereumClient
################################################################################
@click.command('runEC')
def runEC():
    from io import BytesIO
    import pycurl
    import json
    from modicum import EthereumClient as EC
    
    GETH_IP = os.environ.get('GETHIP')
    GETH_PORT = os.environ.get('GETHPORT')
    ethclient = EC.EthereumClient(ip=GETH_IP, port=GETH_PORT)
    response = ethclient.accounts()
    print(response)


################################################################################
# CONTRACT MANAGER CLI
################################################################################
@click.command('runAsCM')
@click.option('--index', default=0, show_default=True)
@click.option('--sim',is_flag=True)
def runAsCM(index,sim):
    from modicum import ContractManager as CM
    thisCM = CM.ContractManager(os.environ.get('CMIP'),index)

    GETH_IP = os.environ.get('GETHIP')
    GETH_PORT = os.environ.get('GETHPORT')

    _CONTRACT_ = os.environ.get('CONTRACTPATH')
    click.echo(_CONTRACT_)

    thisCM.connect(GETH_IP,GETH_PORT,index)

    print(sim,type(sim),)

    if sim:
        print("run simulation")
        thisCM.testrun()
    else:       
        with open(_CONTRACT_) as f:
            BYTECODE = "0x"+f.read()
            thisCM.run(BYTECODE,cfg.CONTRACT_GAS,verbose=False)

@click.command('stopCM')
def stopCM():
    cmeventSender = ctxt.socket(zmq.REQ)

    _CMIP_ = os.environ.get('CMIP')
    cmeventSender.connect("tcp://%s:%s" %(_CMIP_,"10001"))
    msg = {"request": "stop"}
    cmeventSender.send_pyobj(msg)
    response = cmeventSender.recv_pyobj()
    click.echo(response)

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
    _CMIP_ = os.environ.get('CMIP')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    S = Solver.Solver(index)

    S.startCLIListener(7654)

    S.platformConnect(_CMIP_, _GETHIP_,_GETHPORT_,index)

@click.command('stopSolver')
def stopSolver():
    eventSender =ctxt.socket(zmq.REQ)
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
    _CMIP_ = os.environ.get('CMIP')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    M = Mediator.Mediator(index,sim=="True")

    M.startCLIListener(8765)

    M.platformConnect(_CMIP_, _GETHIP_, _GETHPORT_, index)

    # exitcode = M.test(1)


    click.echo("Mediator is registering... ")
    M.register(M.account, "armv7", instructionPrice=1,
               bandwidthPrice=1,availabilityValue=1, verificationCount=1)

    while not M.registered:
        time.sleep(1)
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
        _CMIP_ = host
        _GETHIP_ = host
        _GETHPORT_ = os.environ.get('GETHPORT')
    else:
        _CMIP_ = os.environ.get('CMIP')
        _GETHIP_ = os.environ.get('GETHIP')
        _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CMIP_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    print(playerpath)
    print(index)

    JC = JobCreator.JobCreator(index,sim=="True")
    JC.startCLIListener(cliport=7777)
    JC.platformConnect(_CMIP_, _GETHIP_, _GETHPORT_,index)
    click.echo("Job Creator Daemon is registering... ")
    JC.register(JC.account)
    while not JC.registered:
        time.sleep(1)
    click.echo("JC has registered")

    # mediator = '0x067d6f1ee89b6ccc4a057a19f2071dcdfb42e40c'
    exitcode = JC.addMediator(JC.account, mediator)
    while not JC.mediator:
        time.sleep(1)

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
    _CMIP_ = os.environ.get('CMIP')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CMIP_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    JC = JobCreator.JobCreator()
    JC.startCLIListener(cliport=7777)
    JC.platformConnect(_CMIP_, _GETHIP_, _GETHPORT_,index)
    print("Job Creator Daemon is registering... ")
    exitcode = JC.register(JC.account)
    print("exitcode: %s" %exitcode)
    while not JC.registered:
        time.sleep(1)
    print("JC has registered")

    # mediator = '0x067d6f1ee89b6ccc4a057a19f2071dcdfb42e40c'
    print("Job adding mediator... ")
    exitcode = JC.addMediator(JC.account, mediator)
    while not JC.mediator:
        time.sleep(1)
    

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
                            "arch" : "armv7",
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
                    "arch":"armv7"}


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
def startRP(path,index,host,sim):
    from modicum import ResourceProvider

    if host:
        _CMIP_ = host
        _GETHIP_ = host
        _GETHPORT_ = os.environ.get('GETHPORT')
    else:
        _CMIP_ = os.environ.get('CMIP')
        _GETHIP_ = os.environ.get('GETHIP')
        _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CMIP_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    RP = ResourceProvider.ResourceProvider(index,sim=="True")
    RP.startCLIListener(cliport=9999)
    print("CLI is listening...")

    RP.platformConnect(_CMIP_, _GETHIP_, _GETHPORT_,index)
    print("Resource Provider Daemon is registering... ")
    exitcode = RP.register(RP.account,'armv7', 1)# ratio to 1Gz processor
    print("exitcode:  %s" %exitcode)
    while not RP.registered:
        time.sleep(1)
    print("RP has registered")


    print("Resource Provider adding mediator... ")
    exitcode = RP.addMediator(RP.account, mediator)

    while not RP.mediator:
        time.sleep(1)

    if sim =="True":
        for i in range(100):

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
                   "iroid" : int(i)}

            while not RP.idle:
                time.sleep(1)
            exitcode = RP.postOffer(msg)
        
    else:
        with open(path+"player"+str(index), 'r') as f:
            lines = f.readlines()
            for line in lines:
                print(line)
                call,irid = line.split(" ")                
                
                if call == "postOffer":
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
                        "iroid" : int(irid)
                        }
                    while not RP.idle:
                        time.sleep(1)
                    exitcode = RP.postOffer(msg)
                else:
                    pass

@click.command('startRPDaemon')
@click.option('--index', default=0, show_default=True)
def startRPDaemon(index):
    from modicum import ResourceProvider
    _CMIP_ = os.environ.get('CMIP')
    _GETHIP_ = os.environ.get('GETHIP')
    _GETHPORT_ = os.environ.get('GETHPORT')

    click.echo(_CMIP_)
    click.echo(_GETHIP_)
    click.echo(_GETHPORT_)

    RP = ResourceProvider.ResourceProvider()
    RP.startCLIListener(cliport=9999)
    print("CLI is listening...")

    RP.platformConnect(_CMIP_, _GETHIP_, _GETHPORT_,index)
    print("Resource Provider Daemon is registering... ")
    exitcode = RP.register(RP.account,'armv7', 1)# ratio to 1Gz processor
    print("exitcode:  %s" %exitcode)
    while not RP.registered:
        time.sleep(1)
    print("RP has registered")


    # mediator = '0x067d6f1ee89b6ccc4a057a19f2071dcdfb42e40c'
    print("Resource Provider adding mediator... ")
    exitcode = RP.addMediator(RP.account, mediator)
    while not RP.mediator:
        time.sleep(1)


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
    else:
        click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

main.add_command(foo_command)
main.add_command(build)
main.add_command(run)
main.add_command(runAsCM)
main.add_command(stopCM)
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
main.add_command(runEC)
main.add_command(getSize)

# main.add_command(profile)
