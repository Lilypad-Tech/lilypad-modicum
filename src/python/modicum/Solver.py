#import zmq
import logging
import sys
import os
import time
import datetime
from .PlatformClient import PlatformClient
from . import PlatformStructs as Pstruct
from . import helper

POLLING_INTERVAL = 1 # seconds



class Solver(PlatformClient):
    def __init__(self,index):
        super().__init__()
        self.logger = logging.getLogger("Solver")
        self.logger.setLevel(logging.INFO)
        
        # ch = logging.StreamHandler()
        # # formatter = logging.Formatter("---%(name)s---: \n%(message)s\n\r")
        # formatter = logging.Formatter("---%(name)s---:%(message)s")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.solve = False

        self.mediators = {}
        self.resource_providers = {}
        self.job_creators = {}
        self.resource_offers = {}
        self.job_offers = {}
        self.job_offer_part_one_completed = []
        self.job_offer_part_two_completed = []
        self.matched_jos = {}
        self.matched_ros = {}

        self.index = index


    def register(self, account):
        self.account = account
        self.contract.registerSolver(account)


    def matchable(self, resource_offer, job_offer):

        # Both parts of job offer should have arrived.
        if job_offer.offerId not in self.job_offer_part_one_completed or job_offer.offerId not in self.job_offer_part_two_completed:
            self.logger.info("two parts of offer has not been arrived yet.")
            return (False, False)

        #instructionCap >= instructionLimit
        #print("Begin Matching")
        if resource_offer.instructionCap < job_offer.instructionLimit:
            self.logger.info("Too many instructions: %s < %s"
                            %(resource_offer.instructionCap,job_offer.instructionLimit))
            return(False, False)

        # memoryCap >= ramLimit
        if resource_offer.memoryCap < job_offer.ramLimit:
            self.logger.info("It takes a lot of ram: %s < %s"
                            %(ResourceOffer.memoryCap, job_offer.ramLimit))
            return(False, False)

        #localStorageCap>= localStorageLimit
        if resource_offer.localStorageCap < job_offer.localStorageLimit:
            self.logger.info("Too much disk: %s < %s" %(resource_offer.localStorageCap,job_offer.localStorageLimit))
            return(False, False)

        #bandwidthCap >= bandwidthLimit
        if resource_offer.bandwidthCap < job_offer.bandwidthLimit:
            self.logger.info("Too much data: %s < %s" %(resource_offer.bandwidthCap,job_offer.bandwidthLimit))
            return(False, False)

        #instructionPrice >= instructionMaxPrice
        if resource_offer.instructionPrice > job_offer.instructionMaxPrice:
            self.logger.info("Instructions too expensive: %s > %s" %(resource_offer.instructionPrice,job_offer.instructionMaxPrice))
            return(False, False)

        #bandwidthPrice >= bandwidthMaxPrice
        if resource_offer.bandwidthPrice > job_offer.bandwidthMaxPrice:
            self.logger.info("Data too expensive : %s > %s" %(resource_offer.bandwidthPrice,job_offer.bandwidthMaxPrice))
            return(False, False)

        # if (datetime.datetime.now() + datetime.timedelta(0,0,self.resource_providers[resource_offer.resourceProvider].timePerInstruction  * job_offer.instructionLimit)) > job_offer.completionDeadline:
        self.logger.info("Type: %s" %(time.time() +
            job_offer.instructionLimit *
            self.resource_providers[resource_offer.resourceProvider].timePerInstruction
            ))
        self.logger.info("Type: %s" %job_offer.completionDeadline)


        completionDeadline = time.time() + job_offer.instructionLimit * self.resource_providers[resource_offer.resourceProvider].timePerInstruction

        if completionDeadline > job_offer.completionDeadline:

            self.logger.info("Not Enough Time to complete: %s > %s" %(completionDeadline,job_offer.completionDeadline))
            return(False, False)

        #JO.arch = RP.arch
        if self.resource_providers[resource_offer.resourceProvider].arch != job_offer.arch:
            self.logger.info("Architecture mismatch")
            return(False, False)


        # JO.trustedMediators intersection RP.trustedMediators != empty
        for i in self.resource_providers[resource_offer.resourceProvider].trustedMediators:
            for j in self.job_creators[job_offer.jobCreator].trustedMediators:
                if i == j:
                    #Deposits >=jobDeposit
                    try :
                        sharedMediator = self.mediators[i]
                    except KeyError:
                        self.logger.info("Mutually trusted mediator %s has not registered" %i)
                        continue

                    #necessary price of mediation by mediation
                    mediatorDeposit = job_offer.instructionLimit * sharedMediator.instructionPrice + job_offer.bandwidthLimit * sharedMediator.bandwidthPrice + job_offer.bandwidthLimit * sharedMediator.bandwidthPrice
                    #necessary price of job execution by resource_offer
                    jobDeposit = job_offer.instructionLimit * resource_offer.instructionPrice + job_offer.bandwidthLimit * resource_offer.bandwidthPrice + job_offer.bandwidthLimit * resource_offer.bandwidthPrice
                    #Assume that Fine is 10xprice
                    fineRate = 100 #TODO make finerate global constant
                    fine = fineRate * jobDeposit
                    # if ((resource_offer.deposit > (fine + mediatorDeposit)) and (job_offer.deposit > (fine + mediatorDeposit)) ):
                    return(True,i)

        self.logger.info("No mutually trusted Mediator available") #only will reach here if there is no mediator
        self.logger.info(self.resource_providers[resource_offer.resourceProvider].trustedMediators)
        self.logger.info(self.job_creators[job_offer.jobCreator].trustedMediators)


        return(False, False)

    def bfs(self, resourceList, jobList, edgeList, currentNode, jobsVisited, resourcesVisited, resourceOrJob, prevTraversedJob, prevTraversedResource):
        #Start searching all connected nodes
        if (resourceOrJob == 'resource'):
            #prevTraversedResource.append(currentNode)
            for i in resourceList[currentNode]:
               #if i not in prevTraversedJob:
                if jobsVisited[i] == 0: #i is not visited, free nodes
                    edgeList.append([i,currentNode])
                    return(True, edgeList)
            #recursively search if not found
            for i in resourceList[currentNode]:
                if i not in prevTraversedJob:
                    edgeList2 = edgeList
                    prevTraversedJob2 = prevTraversedResource
                    prevTraversedJob2.append(i)
                    edgeList2.append([i,currentNode])
                    [found, edgeList3] = self.bfs(resourceList, jobList,edgeList2, i, jobsVisited, resourcesVisited, 'job', prevTraversedJob2, prevTraversedResource)
                    if found: #if found == True
                        return(found,edgeList3)

        elif resourceOrJob == 'job':
            #prevTraversedJob.append(currentNode)
            for i in jobList[currentNode]:
                #if i not in prevTraversedResource:
                if resourcesVisited[i] == 0: #i is not visited, free node
                    edgeList.append([currentNode,i])
                    return(True, edgeList)
            #recursively search if not found
            for i in jobList[currentNode]:
                if i not in prevTraversedResource:
                    edgeList2 = edgeList
                    prevTraversedResource2 = prevTraversedResource
                    prevTraversedResource2.append(i)
                    edgeList2.append([currentNode,i])
                    [found, edgeList3 ] = self.bfs(resourceList, jobList,edgeList2, i, jobsVisited, resourcesVisited, 'resource', prevTraversedJob, prevTraversedResource2)
                    if found: #if found == True
                        return(found, edgeList3)

        return(False, [])

    def GreedyMatches(self):
        ros = list(self.resource_offers.keys())
        jos = list(self.job_offers.keys())
        matches = []
        for jo in jos:
            for ro in ros:
                (match, mediator) = self.matchable(self.resource_offers[ro], self.job_offers[jo])
                if match:
                    matches.append((jo, ro, mediator))
                    ros.remove(ro)
                    break
        return matches

        #maximum bipartate matching algorithm
    def HopcroftKarp(self):
        #Create graph
        jobList={}
        resourceList = {}
        mediatorList = {}

        edges = []
        #list of visited nodes
        visitedJob = {}
        visitedResource = {}
        for j in self.resource_offers:
            resourceList[j]=[]
            visitedResource[j]=0

        self.logger.info("#JOs: %s, #RO: %s" %(self.job_offers, self.resource_offers))

        #create edges for each node
        for i in self.job_offers:
            edges = []
            visitedJob[i]=0
            mediatorList[i] = {}
            for j in self.resource_offers:
                [result,mediator] = self.matchable(self.resource_offers[j],self.job_offers[i])
                if (result):
                    self.logger.info("Matchable")
                    edges.append(j)
                    resourceList[j].append(i)
                    mediatorList[i][j]=mediator
                else:
                    self.logger.info("Not Matchable")
            jobList[i] = edges

        #this uses Hopcroft-Karp algorithm for maximal bipartate matchingMediator
        P = []

        for i in jobList:
            [result, newEdges] = self.bfs(resourceList, jobList, [], i, visitedJob, visitedResource, 'job', [i], [])
            if (result != False): #Important step for null results
                for j in newEdges:
                    visitedJob[j[0]]=1
                    visitedResource[j[1]]=1
                    mediator = mediatorList[j[0]][j[1]]
                    j.append(mediator)
                    if result: #if we found a successful graph
                        if j not in P:
                            P.append(j)
                        else:
                            P.remove(j) #Why would you remove it?

        return(P)

    def platformListener(self):
        self.active = True
        self.logger.info("Listening for contract events...")

        while self.active:
            events = self.contract.poll_events()
            for event in events:
                params = event['params']
                name = event['name']
                transactionHash = event['transactionHash']

                self.getReceipt(name, transactionHash)

                self.logger.info("{}({}).".format(name, params))
                if name == "MediatorRegistered":
                    self.logger.info("%s" %name)
                    self.mediators[params['addr']] = Pstruct.Mediator(
                                                        params['arch'],
                                                        params['instructionPrice'],
                                                        params['bandwidthPrice'])

                elif name == "ResourceProviderRegistered":
                    self.logger.info("%s" %name)
                    self.resource_providers[params['addr']] = Pstruct.ResourceProvider(params['arch'], params['timePerInstruction'])
                elif name == "JobCreatorRegistered":
                    self.logger.info("%s" %name)
                    self.job_creators[params['addr']] = Pstruct.JobCreator()
                elif name == "ResourceProviderAddedTrustedMediator":
                    self.logger.info("%s" %name)
                    self.logger.info("name : %s  addr : %s" %(name, params['addr']))
                    self.resource_providers[params['addr']].trustedMediators.append(params['mediator'])
                elif name == "JobCreatorAddedTrustedMediator":
                    self.logger.info("%s" %name)
                    self.job_creators[params['addr']].trustedMediators.append(params['mediator'])
                elif name == "ResourceOfferPosted":
                    self.logger.info("%s = %s" %(name, params["iroid"]))
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

                    self.resource_offers[params['offerId']] = offer
                elif "JobOfferPosted" in name:

                    self.logger.info("%s offerID = %s" % (name, params['offerId']))

                    if "One" in name:
                        self.logger.info("%s = %s" % (name, params['ijoid']))
                        self.logger.info("completionDeadline: %s Type: %s" %(params['completionDeadline'],type(params['completionDeadline'])))

                    helper.storeJobOffer(event,self.job_offers)

                    if name == "JobOfferPostedPartOne":
                        self.job_offer_part_one_completed.append(params['offerId'])
                    if name == "JobOfferPostedPartTwo":
                        self.job_offer_part_two_completed.append(params['offerId'])

                elif name == "Matched":
                    # self.logger.info("I: %s" %name)

                    joid = params['jobOfferId']
                    roid = params['resourceOfferId']

                    self.logger.info("I: job offer %s matchID = %s" %(name, joid))
                    self.logger.info("I: resource offer %s matchID = %s" %(name, roid))



                    ijoid = self.matched_jos[joid].ijoid
                    iroid = self.matched_ros[roid].iroid

                    self.logger.info("I: job offer %s = %s" %(name, ijoid))
                    self.logger.info("I: resource offer %s = %s" %(name, iroid))

                    self.helper.logEvent(self.index, name, self.ethclient, event['transactionHash'], joid=joid, ijoid=ijoid)


            #after reading events call mathing

            matches = self.HopcroftKarp()
            # matches = self.GreedyMatches()
            if matches:
                self.logger.info(matches)
                self.logger.info(self.resource_providers)
                self.logger.info(self.resource_offers)
                self.logger.info(self.job_creators)
                self.logger.info(self.job_offers)
            for i in matches:
                self.logger.info("I: postMatch job offer = %s" %self.job_offers[i[0]].ijoid)
                self.logger.info("I: postMatch resource offer = %s" %self.resource_offers[i[1]].iroid)

                self.logger.info("jo id: %s" %self.job_offers[i[0]].offerId)
                self.logger.info("ro id: %s" %self.resource_offers[i[1]].offerId)
                txHash = self.contract.postMatch(self.account,  True,
                                        self.job_offers[i[0]].offerId,
                                        self.resource_offers[i[1]].offerId,
                                        i[2])
                #remove matches from list
                self.matched_jos[i[0]] = self.job_offers.pop(i[0])
                self.matched_ros[i[1]] = self.resource_offers.pop(i[1])
            
            self.wait()
            
