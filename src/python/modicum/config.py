# deployment
#DIRECTORY_ADDRESS = 'tcp://127.0.0.1:10001'
import sys
import os
import fabric.api as fabi

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# import config_main as cfg
# import config_private as private

CONTRACT_GAS = "0x1000000000"
# TRANSACTION_GAS = "0x1000000"
TRANSACTION_GAS = 2000000
                    #5205164
                    #5169695
NUM_TYPES =9999999999999;
PRECISION = 4294967296;
MAX_QUANTITY = 100;
START_INTERVAL = 1;
END_INTERVAL = 100;
INTERVAL_LENGTH = 60;
SOLVING_INTERVAL = 5;
POLLING_INTERVAL = 1 # seconds Used in actor to determin how often to check for events

# MINER_IP = '172.21.20.34'
# MINER_PORT = '10000'
# DIR_IP = '172.21.20.34'
# SOLVER_IP = '172.21.20.34'
# RECORDER_IP = '172.21.20.34'
