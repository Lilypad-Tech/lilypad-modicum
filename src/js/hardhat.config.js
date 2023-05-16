require('hardhat-ethernal');
require('@nomicfoundation/hardhat-toolbox');

if(!process.env.ETHERNAL_EMAIL) {
  console.error('Please set ETHERNAL_EMAIL environment variable')
  process.exit(1)
}

if(!process.env.ETHERNAL_PASSWORD) {
  console.error('Please set ETHERNAL_PASSWORD environment variable')
  process.exit(1)
}

const config = {
  solidity: '0.8.17',
  defaultNetwork: 'hardhat',
  ethernal: {
    email: process.env.ETHERNAL_EMAIL,
    password: process.env.ETHERNAL_PASSWORD,
  },
  networks: {
    hardhat: {
      blockGasLimit: 68719476736000,
    },
    localhost: {}
  },
};

extendEnvironment((hre) => {
  hre.ethernalSync = true;
  hre.ethernalWorkspace = 'modicum-demo';
  hre.ethernalTrace = false;
  hre.ethernalResetOnStart = 'modicum-demo';
});

module.exports = config;
