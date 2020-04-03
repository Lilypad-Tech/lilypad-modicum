import logging
import fabric.api as fabi
import zmq
import subprocess
import pwd
import grp

class DirectoryClient():
    def __init__(self):
        self.logger = logging.getLogger("Directory Client")
        self.context = zmq.Context()

    def test(self):
        print("OK")

    def fabput(self,local,remote):
        fabi.put(local,remote,mode="0754")

    def fabget(self,local,remote):
        fabi.get(remote, local)

    def fabrun(self, cmd):
        results = ''
        with fabi.hide('output', 'running', 'warnings', 'aborts'), fabi.settings(warn_only=True):
            results = fabi.run(cmd)
        return results

    def publishData(self,host,port,user,localpath,tag,name,ijid,sshpath):
        '''sftp job to directory'''
        remotePath = "/home/%s/%s/" %(user,tag)
        
        self.logger.info([host,port,user,tag,localpath,sshpath,remotePath])
        # , "--chmod=666"
        # args = ["rsync", "-arv", 
        #         "--include", "%s/" %(name),
        #         "--include", "%s/*" %(name),
        #         "--include", "%s.tar" %(tag),
        #         "--exclude", "*",
        #         "-e", "ssh -oStrictHostKeyChecking=no -p 222 -i %s" %(sshpath), 
        #         "%s/" %(localpath),
        #         "%s@%s:%s" %(user,host,remotePath)                
        #         ]
        args = ["rsync", "-arv",
                "--include", "%s.tar" %(tag),
                "--exclude", "*",
                "-e", "ssh -oStrictHostKeyChecking=no -p 222 -i %s" %(sshpath), 
                "%s/" %(localpath),
                "%s@%s:%s" %(user,host,remotePath)                
                ]
        print(args)
        subprocess.run(args,check=True)

        remotePath = "/home/%s/%s/%s" %(user,tag,name+str(ijid))
        args = ["rsync", "-arv",
                "-e", "ssh -oStrictHostKeyChecking=no -p 222 -i %s" %(sshpath), 
                "%s/%s/" %(localpath,name),
                "%s@%s:%s" %(user,host,remotePath)                
                ]
        print(args)
        subprocess.run(args,check=True)


        self.logger.info("done")

    def publishResult(self,host,port,user,localpath,tag,name,ijoid,sshpath):
        '''sftp job to directory'''
        remotePath = "/home/%s/%s/%s" %(user, tag, name+str(ijoid))

        self.logger.info([host,port,user,tag,localpath,sshpath,remotePath])
        # , "--chmod=666"
        args = ["rsync", "-arv",
                "--rsync-path", "mkdir -p %s && rsync" %remotePath,
                "-e", "ssh -oStrictHostKeyChecking=no -p 222 -i %s" %(sshpath), 
                "%s" %(localpath),
                "%s@%s:%s" %(user,host,remotePath)                
                ]
        print(args)
        subprocess.run(args,check=True)


        self.logger.info("done")

    def getResult(self,host,sshport,user,remote_user,tag,name,ijoid,localPath,sshpath):

        '''sftp job to directory'''
        remotePath = "/home/%s/%s/%s/output" %(remote_user,tag,name+str(ijoid))

        self.logger.info([host,sshport,user,remote_user,tag,name,ijoid,localPath,sshpath])
        # , "--chmod=666"
        args = ["rsync", "-arv",
                "-e", "ssh -oStrictHostKeyChecking=no -p 222 -i %s" %(sshpath),
                "%s@%s:%s" %(user,host,remotePath),
                "%s" %(localPath)
                ]
        print(args)

        try:
            subprocess.run(args, check=True)
            return 0
        except subprocess.CalledProcessError as e:

            groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
            gid = pwd.getpwnam(user).pw_gid
            groups.append(grp.getgrgid(gid).gr_name)

            self.logger.info("%s is in groups %s" % (user, groups))
            self.logger.info("%s is not in %s group" % (user, tag))

            self.logger.error(e)

            return 1



    def getData(self,host,sshport,user,remote_user,tag,name,ijoid,localPath,sshpath):
        '''sftp job from directory'''
        self.logger.info("actor getData")
        
        remotePath = "/home/%s/%s/" %(remote_user,tag)
        
        self.logger.info([host,sshport,user,remote_user,tag,name,ijoid,localPath,sshpath,name+str(ijoid)])

        args = ["rsync", "-arv", 
                "--include", "%s/" %(name+str(ijoid)),
                "--include", "%s/*" %(name+str(ijoid)),
                "--include", "%s.tar" %(tag),
                "--exclude", "*",
                "-e", "ssh -oStrictHostKeyChecking=no -p 222 -i %s" %(sshpath),                 
                "%s@%s:%s" %(user,host,remotePath),    
                "%s" %(localPath)        
                ]
        print(args)
        subprocess.run(args,check=True)


        # fabi.env.key_filename = sshpath
        # fabi.execute(self.fabget, localPath, remotePath, hosts=user+"@"+host+":"+sshport)



    def getPermission(self,host,port,ID,job,pubkey):
        '''send getPermission request to Directory service at ip:port'''
        directory_socket = self.context.socket(zmq.REQ)
        print(host)
        directory_socket.connect("tcp://%s:%s" %(host,port))
        msg = {
          'request': "get_permission",
          "ID":ID,
          "job": job,
          "pubkey":pubkey
        }
        directory_socket.send_pyobj(msg)
        message = directory_socket.recv_pyobj()
        print(message)
        return message


    def getSize(self, host, sshport,user, remote_user, job, sshpath):
        '''get size of files to download'''
        remotePath = "/home/%s/%s/" %(remote_user,job)
        self.logger.info(remotePath)
        fabi.env.key_filename = sshpath
        host = user+"@"+host+":"+sshport
        # result = fabi.execute(self.fabrun, 'du -s %s | awk \'{print $1;}\'' %remotePath, hosts=host)
        result = fabi.execute(self.fabrun, 'du -abc %s' %remotePath, hosts=host)

        return result[host]

    def getUsername(self, host, cliport, remoteID):
        self.logger.info("get username of wallet")
        directory_socket = self.context.socket(zmq.REQ)
        directory_socket.connect("tcp://%s:%s" %(host,cliport))
        msg = {
            'request' : "get_username",
            'ID' : remoteID
        }
        directory_socket.send_pyobj(msg)
        remote_user = directory_socket.recv_pyobj()
        self.logger.info("remote username: %s" %remote_user)
        return remote_user
