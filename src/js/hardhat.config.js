require('@nomicfoundation/hardhat-toolbox');

const config = {
  solidity: '0.4.25',
  defaultNetwork: 'hardhat',
  networks: {
    hardhat: {
      blockGasLimit: 68719476736000,
    },
    localhost: {}
  },
};

module.exports = config;
