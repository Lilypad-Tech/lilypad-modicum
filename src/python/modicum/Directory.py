import os
import pwd
import grp
from threading import Thread
import logging
import fabric as fabi
import zmq

from . import DockerWrapper as DW

class Directory():
    def __init__(self):
        self.logger = logging.getLogger("Directory")
        self.logger.setLevel(logging.INFO)
       
        # ch = logging.StreamHandler()
        # # formatter = logging.Formatter("---%(name)s---: \n%(message)s\n\r")
        # formatter = logging.Formatter("---%(name)s---:%(message)s")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.whitelist = {}
        self.isParent = True

    def startServer(self,port,childport):
        self.zmqcontext = zmq.Context()

        #Setup socket for new actor connections
        self.socket = self.zmqcontext.socket(zmq.REP)
        self.logger.info("Listening Port: %s" %port)
        self.socket.bind("tcp://*:%s" %port)

        # Directory event handler thread
        thread = Thread(target=self.eventHandler)
        thread.start()

    def eventHandler(self):
        '''listen for messages from actors'''
        while self.isParent:
            msg = self.socket.recv_pyobj()
            self.logger.info("Directory received message: %s" %msg)

            if msg['request'] == 'get_permission':
                ID = msg["ID"]
                job = msg["job"]
                pubkey = msg["pubkey"]
                self.getPermission(ID,job,pubkey)

            # elif msg['request'] == "get_size":
            #     # if ID not in self.whitelist:
            #     #     self.socket.send_pyobj("invalid user")
            #     # else:
            #     job = msg["job"]
            #     ID = msg["ID"]
            #     user = "user_%s" %(ID)
            #     start_path="/home/%s/%s" %(user,job)
            #     # start_path = "/home/user_2/matrix_multiplication/"
            #     self.logger.info(start_path)
            #     size = self.getSize(start_path)
            #     self.socket.send_pyobj(size)

            elif msg['request'] == "get_username":
                self.logger.info("get username")
                ID = msg['ID']
                username = self.whitelist[ID]["user"]
                self.socket.send_pyobj(username)

            elif msg["request"] == "stop":
                self.logger.info("stop Directory")
                self.isParent = False
                self.socket.send_pyobj("Directory stopped")
                # self.socket.close()
                # self.zmqcontext.term()


    def getPermission(self,ID,job,pubkey):
        '''check if id is in list, if not add, create folder'''
        # check for user in system
        user = "user"+ID[-10:]
        if ID not in self.whitelist:
            self.whitelist[ID] = {"pubkey":pubkey,
                                  "user" : user}

            #create user
            exists = os.system("id -u %s" %user)
            self.logger.info("%s exists? : %s"%(user, exists==0))
            if exists != 0:
                self.logger.info("Create user")
                exists = os.system("useradd %s" %user)
            if exists==0:
                #get uid of new user
                uid = pwd.getpwnam(user).pw_uid
                self.logger.info("uid: %s" %uid)
                self.whitelist[ID]["uid"]=uid
                #get gid of new user
                gid = grp.getgrnam(user).gr_gid
                self.whitelist[ID]["gid"]=gid

                #create home directory
                os.makedirs("/home/%s"%user,0o751, True)

                #transfer ownership of new home to new user
                os.chown("/home/%s/" %user,uid,gid)

                newpid = os.fork()
                if newpid == 0:
                    self.isParent = False
                    #Change ugetPermissionser
                    os.setgroups([])
                    os.setgid(gid)
                    os.setuid(uid)

                    #create .ssh folder
                    os.makedirs("/home/%s/.ssh" %(user),0o700,True)

                    #add pubkey to authorized_keys
                    os.system("echo '%s' > /home/%s/.ssh/authorized_keys" %(pubkey, user))

                    #update permission on authorized_keys
                    os.chmod("/home/%s/.ssh/authorized_keys"%user, 0o600)
                else:
                    pass

                if job is not None and self.isParent:
                    self.logger.info("%s needs access to %s" %(ID, job))
                    group = "group_%s"%(job)
                    self.logger.info("group:%s"%group)
                    os.system("groupadd %s" %(group))
                    self.logger.info("group added")
                    gid = grp.getgrnam(group).gr_gid
                    self.logger.info("gid: %s" %gid)
                    self.whitelist[ID]["job"] = {"name": job}
                    self.whitelist[ID]["job"]["gid"] = gid

                    uid = pwd.getpwnam(user).pw_uid
                    self.logger.info("uid: %s" %uid)
                    os.system("usermod -a -G %s %s" %(group,user))

                    newpid = os.fork()
                    if newpid == 0:
                        self.isParent = False

                        self.logger.info("update ids")
                        os.setgroups([])
                        os.setgid(gid)
                        os.setuid(uid)



                        os.makedirs("/home/%s/%s" %(user,job), 0o750,True)
                        os.chown("/home/%s/%s" %(user,job),uid,gid)
                        # self.setPermission(ID,job)
                    else:

                        groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
                        gid = pwd.getpwnam(user).pw_gid
                        groups.append(grp.getgrgid(gid).gr_name)

                        self.logger.info("%s is in group %s" % (user, groups))


                        self.logger.info("user is : %s" %user)
                        msg = {"exitcode" : 0,
                               "user" : user,
                               "groups" : groups}


                        self.socket.send_pyobj(msg)
                        '''BELOW IS FOR TESTING ONLY'''
                        # self.isParent = False
            else:
                self.logger.info("Failed to add")
                self.socket.send_pyobj("Failed to add")
        else:

            groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
            gid = pwd.getpwnam(user).pw_gid
            groups.append(grp.getgrgid(gid).gr_name)

            self.logger.info("%s is in group %s" % (user, groups))


            msg = {"exitcode" : 0,
                   "user" : user,
                   "groups": groups}
            self.socket.send_pyobj(msg)

    def setPermission(self,ID,job):
        path = "/home/%s/%s" %(user,job)
        os.system("chgrp -R group_matrix_multiplication %s"%path)

    def revokePermission(self,ID):
        '''remove id from list'''
    # def getSize(self,start_path):
    #     '''get size of files to be transferred'''
    #     total_size = 0
    #     for dirpath, dirnames, filenames in os.walk(start_path):
    #         for f in filenames:
    #             fp = os.path.join(dirpath, f)
    #             total_size += os.path.getsize(fp)
    #     return total_size
