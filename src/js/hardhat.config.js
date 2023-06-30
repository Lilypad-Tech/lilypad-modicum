require('hardhat-deploy');
require('@nomicfoundation/hardhat-toolbox');

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
    localhost: {}
  },
};

module.exports = config;
