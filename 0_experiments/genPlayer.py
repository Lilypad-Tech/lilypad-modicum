def genPlayer(kind, player, numJobs):

    if kind == "JC":
        with open(player, 'w+') as f:
            for i in range (numJobs-1):
                str1 = "publish /home/riaps/projects/MODiCuM/workloads/bodytrack/job bodytrack run %s NA END\n" %(i+1)
                str2 = "postOffer /home/riaps/projects/MODiCuM/workloads/bodytrack/job bodytrack run %s False END\n" %(i+1)
                f.write(str1)
                f.write(str2)
            str1 = "publish /home/riaps/projects/MODiCuM/workloads/bodytrack/job bodytrack run %s NA END\n" %(i+2)
            str2 = "postOffer /home/riaps/projects/MODiCuM/workloads/bodytrack/job bodytrack run %s False END" %(i+2)
            f.write(str1)
            f.write(str2)

    elif kind == "RP":
        with open(player, 'w+') as f:
            for i in range (numJobs-1):
                str1 = "postOffer %s\n" %(i+1)
                f.write(str1)
            str1 = "postOffer %s" %(i+2)
            f.write(str1)



genPlayer("JC", "player4", 100)
genPlayer("RP", "player7", 100)