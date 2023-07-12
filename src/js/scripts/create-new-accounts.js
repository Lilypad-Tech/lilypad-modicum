var Wallet = require('ethereumjs-wallet').default

const names = [
  // deploys the contracts
  'ADMIN',
  'FAUCET',
  'SOLVER',
  'MEDIATOR',
  'RESOURCE_PROVIDER',
  'JOB_CREATOR',
]

names.forEach(name => {
  const wallet = Wallet.generate();
  console.log(`export PRIVATE_KEY_${name}=${wallet.getPrivateKeyString()}`)
  console.log(`export ADDRESS_${name}=${wallet.getAddressString()}`)
})
