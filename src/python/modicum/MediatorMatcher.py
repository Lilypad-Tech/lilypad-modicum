#import zmq
import logging
import sys
import os
from time import time, sleep
import datetime
from . import PlatformClient
from . import PlatformStructs

POLLING_INTERVAL= 1 # seconds

## TODO:STEPS FOR MEDIATOR MATCHER
#Listen for events
    #Record matches
    #look for jobResults
    #assign contested jobResults to mediators
#Match Results to their matching mediator (from jobMatch)


class MediatorMatcher():
    def __init__(self, geth_ip, port, directory_ip):
        logging.info("connecting to Platform")
        PC = PlatformClient.PlatformClient()
        '''self.client,self.contract = PC.ethereumConnect(manager_ip=directory_ip, geth_ip=geth_ip, geth_port=port)'''

        self.mediators = {}
        self.matches = {}
        self.job_creators = {}
        self.resource_providers = {}
        self.job_offers =  {}
        self.resource_offers =  {}
        self.matches = {}
        super(MediatorMatcher, self).__init__()

    def match(self, matchId, mediator):
        #TODO PUSH job to Mediator
        return()

    def run(self):
        logging.info("Entering main loop...")
        next_polling = time() + POLLING_INTERVAL
        while True:
            logging.debug("Polling events...")
            for event in self.contract.poll_events():
               name = event['name'] #name of event
               params=event['params'] #parameters of event
               logging.info("{}({}).".format(name, params))
               if name == "MediatorRegistered":
                 self.mediators[params['addr']] = Mediator(params['arch'], params['instructionPrice'], params['bandwidthPrice'], params['dockerBandwidthPrice'])
               elif name == "resourceProviderRegistered":
                 self.resource_providers[params['addr']] = ResourceProvider(params['arch'], params['timePerInstruction'])
               elif name == "jobCreatorRegistered":
                 self.job_creators[params['addr']] = JobCreator()
               elif name == "ResourceProviderAddedTrustedMediator":
                 self.resource_providers[params['addr']].trustedMediators.append(params['mediator'])
               elif name == "JobCreatorAddedTrustedMediator":
                 self.job_creators[params['addr']].trustedMediators.append(params['mediator'])
               elif name == "resourceOfferPosted":
                 offer  = ResourceOffer(params['offerId'], params['addr'], params['instructionPrice'], params['instructionCap'], params['memoryCap'], params['localStorageCap'], params['bandwidthCap'], params['bandwidthPrice'], params['dockerBandwidthCap'], params['dockerBandwidthPrice'], params['deposit'] )
                 self.resource_offers[params['addr']] =  offer
               elif name == "jobOfferPosted":
                 offer = JobOffer(params['offerId'], params['addr'], params['size'], params['arch'], params['instructionLimit'], params['ramLimit'], params['localStorageLimit'], params['bandwidthLimit'], params['instructionMaxPrice'], params['bandwidthMaxPrice'], params['dockerBandwidthMaxPrice'], params['completionDeadline'], params['deposit'])
                 self.job_offers[params['addr']] = offer
               elif name == "matched":
                 self.matches[params['jobOfferId']] = Match(params['jobOfferId'], params['resourceOfferId'], params['mediator'])
               elif name == "jobAssignedForMediation":
                 targetMed = self.matches[params['matchId']].mediator
