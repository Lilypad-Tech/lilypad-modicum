import logging
import zmq
import subprocess
import pwd
import grp

class DirectoryClient():
    def __init__(self):
        self.logger = logging.getLogger("Directory Client")

    def test(self):
        print("OK")

    def fabput(self,local,remote):
        pass

    def fabget(self,local,remote):
        pass

    def fabrun(self, cmd):
        pass

    def publishData(self,host,port,user,localpath,tag,name,ijid,sshpath):
        pass

    def publishResult(self,host,port,user,localpath,tag,name,ijoid,sshpath):
        pass

    def getResult(self,host,sshport,user,remote_user,tag,name,ijoid,localPath,sshpath):
        pass

    def getData(self,host,sshport,user,remote_user,tag,name,ijoid,localPath,sshpath):
        pass

    def getPermission(self,host,port,ID,job,pubkey):
        # fake iit
        return {"user": "bob", "groups": ["foop"], "exitcode": 0}

    def getSize(self, host, sshport,user, remote_user, job, sshpath):
        return 0

    def getUsername(self, host, cliport, remoteID):
        return "bob"