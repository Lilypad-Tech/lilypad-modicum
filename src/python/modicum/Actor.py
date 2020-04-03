import logging

class Actor():
    # def __init__(self,username, password):
    def __init__(self):
        self.logger = logging.getLogger("Actor")

    def profile(self):
        '''https://github.com/delcypher/docker-stats-on-exit-shim'''
        '''https://github.com/collectd/collectd'''

class ResourceProvider(Actor):
    def __init__(self):
        super().__init__()

class JobCreator(Actor):
    def __init__(self):
        super().__init__()
