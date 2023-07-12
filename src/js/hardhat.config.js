require('hardhat-deploy');
require('@nomicfoundation/hardhat-toolbox');
const dotenv = require('dotenv')
dotenv.config({ path: process.env.DOTENV_CONFIG_PATH || '../../.env' })

if(!process.env.PRIVATE_KEY_ADMIN) {
  console.error(`PRIVATE_KEY_ADMIN is not set in .env file`)
  process.exit(1)
}

const config = {
  solidity: '0.4.25',
  defaultNetwork: 'hardhat',
  namedAccounts: {
    deployer: {
      default: 0,
    }
  },
  networks: {
    hardhat: {
      blockGasLimit: 68719476736000,
    },
    localhost: {},
    localgeth: {
      url: 'http://localhost:8545',
      chainId: 1337,
      accounts: [
        process.env.PRIVATE_KEY_ADMIN,
      ],
      blockGasLimit: 68719476736000,
    },
    production: {
      url: 'http://testnet.lilypadnetwork.org:8545',
      chainId: 1337,
      accounts: [
        process.env.PRIVATE_KEY_ADMIN,
      ],
      blockGasLimit: 68719476736000,
    }
  },
};

module.exports = config;
