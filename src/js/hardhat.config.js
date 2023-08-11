require('hardhat-deploy');
require('@nomicfoundation/hardhat-toolbox');
const {
  getAccounts
} = require('./accounts')

const dotenv = require('dotenv')
const ENV_FILE = process.env.DOTENV_CONFIG_PATH || '../../.env'
dotenv.config({ path: ENV_FILE })

const {
  namedAccounts,
  allAccounts,
} = getAccounts()

const config = {
  solidity: '0.8.6',
  defaultNetwork: 'localgeth',
  namedAccounts,
  networks: {
    hardhat: {
      blockGasLimit: 68719476,
      baseFeePerGas: 1000,
      maxPriorityFeePerGas: 2000,
      maxFeePerGas: 10000,
    },
    localhost: {},
    localgeth: {
      url: 'http://localhost:8545',
      chainId: 1337,
      accounts: allAccounts,
    },
    production: {
      url: 'http://testnet.lilypadnetwork.org:8545',
      chainId: 1337,
      accounts: allAccounts,
    },
    ipc: {
      url: 'http://alpha.subnet.ipc.space:2346/rpc/v1',
      chainId: 2734332491184961,
      accounts: allAccounts,
    },
    calibration: {
      url: 'https://api.calibration.node.glif.io',
      chainId: 314159,
      accounts: allAccounts,
    }
  },
};

module.exports = config;
