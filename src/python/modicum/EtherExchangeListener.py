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


class EtherExchangeListener(PlatformClient):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("EtherExchangeListener")
        # logging.config.fileConfig(os.path.dirname(__file__)+'/Modicum-log.conf')
        self.logger.setLevel(logging.INFO)
        
        # ch = logging.StreamHandler()
        # formatter = logging.Formatter("---%(name)s---: \n%(message)s\n\r")
        # ch.setFormatter(formatter)
        # self.logger.addHandler(ch)

        self.job_offers = {}
        self.resource_offers = {}
        self.registered = False

        self.myMatches = {}

        path = dotenv.find_dotenv('.env', usecwd=True)
        dotenv.load_dotenv(path)

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

                if name == 'EtherTransferred':
                    self.logger.info(f'{params["_from"]} - {params["to"]} - {params["value"]} - {params["cause"]}')

            self.wait()
