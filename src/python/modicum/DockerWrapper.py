import os
import docker
import requests
import logging
import tqdm


def getDockerClient():
    dockerClient = docker.from_env(timeout=300)
    return dockerClient

def getDockerAPIClient():
    dockerAPIclient = docker.APIClient(base_url='unix://var/run/docker.sock')
    return dockerAPIclient

def login(client,username,password):
    try:
        client.login(username, password)
    except requests.exceptions.ConnectionError as e:
        logging.info("Try with sudo")


def buildImage(client,path, tag):
    '''Build docker image called <tag> from Dockerfile at <path>'''
    image = client.images.build(path=path, tag=tag)[0]
    return image

def saveImage(path, tag, image):
    '''Documentation is a bit flakey on this: https://github.com/docker/docker-py/issues/1595
    https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.Image.save'''
    os.makedirs(path, exist_ok=True)
    filepath = path+tag

    gen = image.save(chunk_size=None, named=True)
    with open(filepath, 'w+b') as tarf:
        for chunk in tqdm.tqdm(gen):
            tarf.write(chunk)

    # os.system("sudo docker image save -o %s %s" %(path, tag))
def loadImage(client,path):
    with open(path, 'rb', ) as tarf:
        images = client.images.load(tarf)
        return images

def getImageHash(image):
    jobHash = image.id.split(":")[1] #strip off sha256 prefix
    jobHash_int = int(jobHash, 16)
    return jobHash_int

def runContainer(client,tag,name, xdict):
        container = client.containers.run(image=tag, name=name, volumes=xdict["mounts"],
                              environment=xdict["env"], auto_remove=True,
                              detach=True, command=xdict["command"])
        return container


def runContainer_old(client,tag, name, input,output,appinput,appoutput,perf_enabled=False):
    if perf_enabled:
        os.system("sudo perf stat \
                    docker run --rm \
                    --mount type=bind,source=%s,target=%s\
                    --mount type=bind,source=%s,target=%s\
                    -e \"MODICUM_INPUT=%s\" \
                    -e \"MODICUM_OUTPUT=%s\" \
                    %s >> perf.log" %(input,appinput,output,appoutput,appinput,appoutput,tag))
    else:
        mounts = {
                    input : {'bind':appinput,'mode':'ro'},
                    output: {'bind':appoutput,'mode':'rw'}
                }

        env = {
                'MODICUM_INPUT':appinput,
                'MODICUM_OUTPUT':appoutput
            }
        container = client.containers.run(image=tag, name=name, volumes=mounts,
                              environment=env, auto_remove=True,
                              detach=True, command=["python3","matrix.py"])
        return container


def publishImage(client,tag):
    '''Publish image to Docker Trusted Registry'''
    for line in client.images.push(tag, stream=True):
        logging.info (line)

def getImageDigest(apiclient,tag):
    '''Get data from image. Not sure which hash to use: https://github.com/docker/distribution/issues/1662'''
    image_dict = apiclient.inspect_image(tag)
    print(image_dict)
    # repoDigestSha = image_dict["RepoDigests"][0]
    IDsha = image_dict["Id"].split(":")[1]
    IDint = int(IDsha, 16)
    size = image_dict["Size"] #in bytes
    os = image_dict["Os"]
    arch = image_dict["Architecture"]
    digest = {"hash":IDsha,"size":size, "arch":arch}
    return digest

def pullImage(client,tag):
    '''Get Docker image from Registry'''
    try:
        image = client.images.pull(tag)
        return(image)
    except requests.exceptions.HTTPError as e:
        logging.info(e)

def test():
    print("test ok")


# class DockerWrapper():
#     def getDockerClient(self):
#         dockerClient = docker.from_env()
#         return dockerClient
#
#     def getDockerAPIClient(self):
#         dockerAPIclient = docker.APIClient(base_url='unix://var/run/docker.sock')
#         return dockerAPIclient
#
#     def login(self,client,username,password):
#         try:
#             client.login(username, password)
#         except requests.exceptions.ConnectionError as e:
#             logging.info("Try with sudo")
#
#
#     def buildImage(self,client,path, tag):
#         '''Build docker image called <tag> from Dockerfile at <path>'''
#         image = client.images.build(path=path, tag=tag)[0]
#         return image
#
#     def saveImage(self,path, image):
#         '''Documentation is a bit flakey on this: https://github.com/docker/docker-py/issues/1595
#         https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.Image.save'''
#         gen = image.save(chunk_size=None)
#         with open(path, 'wb') as tarf:
#             for chunk in tqdm.tqdm(gen):
#                 tarf.write(chunk)
#
#     def runContainer(self,client,tag, name, input,output,appinput,appoutput,perf_enabled=False):
#         if perf_enabled:
#             os.system("sudo perf stat \
#                         docker run --rm \
#                         --mount type=bind,source=%s,target=%s\
#                         --mount type=bind,source=%s,target=%s\
#                         -e \"MODICUM_INPUT=%s\" \
#                         -e \"MODICUM_OUTPUT=%s\" \
#                         %s >> perf.log" %(input,appinput,output,appoutput,appinput,appoutput,tag))
#         else:
#             mounts = {
#                         input : {'bind':appinput,'mode':'ro'},
#                         output: {'bind':appoutput,'mode':'rw'}
#                     }
#
#             env = {
#                     'MODICUM_INPUT':appinput,
#                     'MODICUM_OUTPUT':appoutput
#                 }
#             client.containers.run(image=tag, name=name, volumes=mounts, environment=env, auto_remove=True)
#
#
#     def publishImage(self,client,tag):
#         '''Publish image to Docker Trusted Registry'''
#         for line in client.images.push(tag, stream=True):
#             logging.info (line)
#
#     def getImageDigest(self,apiclient,tag):
#         '''Get data from image. Not sure which hash to use: https://github.com/docker/distribution/issues/1662'''
#         image_dict = apiclient.inspect_image(tag)
#         print(image_dict)
#         # repoDigestSha = image_dict["RepoDigests"][0]
#         IDsha = image_dict["Id"].split(":")[1]
#         IDint = int(IDsha, 16)
#         size = image_dict["Size"] #in bytes
#         os = image_dict["Os"]
#         arch = image_dict["Architecture"]
#         digest = {"hash":IDsha,"size":size, "arch":arch}
#         return digest
#
#     def pullImage(self,client,tag):
#         '''Get Docker image from Registry'''
#         try:
#             image = client.images.pull(tag)
#             return(image)
#         except requests.exceptions.HTTPError as e:
#             logging.info(e)
#
#     def test():
#         print("test ok")
