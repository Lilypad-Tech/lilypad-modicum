require('hardhat-deploy');
require('@nomicfoundation/hardhat-toolbox');
const dotenv = require('dotenv')
dotenv.config({ path: process.env.DOTENV_CONFIG_PATH || './.env' })

if(!process.env.ADMIN_PRIVATE_KEY) {
  console.error(`ADMIN_PRIVATE_KEY is not set in .env file`)
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
        process.env.ADMIN_PRIVATE_KEY,
      ],
      blockGasLimit: 68719476736000,
    },
    production: {
      url: 'http://34.30.95.3:8545',
      chainId: 1337,
      accounts: [
        process.env.ADMIN_PRIVATE_KEY,
      ],
      blockGasLimit: 68719476736000,
    }
  },
};

module.exports = config;
