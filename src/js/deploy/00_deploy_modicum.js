const hre = require('hardhat')
const bluebird = require('bluebird')

const {
  ethers: {
    BigNumber,
  }
} = hre

const {
  getWallet,
} = require('../accounts')

const DEPOSIT_MULTIPLE = 10

// this is in ETH
const JOB_COST = 1

const MODULES = [
  'stable_diffusion:v0.0.1',
  'cowsay:v0.0.1',
  'filecoin_data_prep:v0.0.1',
  'deterministic_wasm:v0.0.1',
]

module.exports = async ({getNamedAccounts, deployments}) => {
  const {deploy} = deployments
  const {admin} = await getNamedAccounts()
  await deploy('Modicum', {
    from: admin,
    args: [],
    log: true,
  });
  const deploymentModicum = await deployments.get('Modicum')

  console.log('--------------------------------------------')
  console.log('--------------------------------------------')
  console.log('--------------------------------------------')
  console.log(`DEPLOYED MODICUM: ${deploymentModicum.address}`)

  const ModicumFactory = await ethers.getContractFactory("Modicum")
  const modicumContract = ModicumFactory.attach(deploymentModicum.address)
  const adminWallet = getWallet('admin')
  const mediatorAccount = getWallet('mediator')
  const adminSigner = adminWallet.connect(hre.ethers.provider)
  const trxMediators = await modicumContract
    .connect(adminSigner)
    .setDefaultMediators([
      mediatorAccount.address,
    ])
  const receipt = await trxMediators.wait()
  console.log(`add mediator trx: ${JSON.stringify(trxMediators)}`)
  console.log(`add mediator receipt: ${JSON.stringify(receipt)}`)

  await modicumContract
    .connect(adminSigner)
    .setResourceProviderDepositMultiple(BigNumber.from(DEPOSIT_MULTIPLE))

  await bluebird.mapSeries(MODULES, async (moduleName) => {
    const trx = await modicumContract
      .connect(adminSigner)
      .setModuleCost(moduleName, ethers.utils.parseEther(`${JOB_COST}`))
    const receipt = await trx.wait()
    console.log(`register module trx: ${JSON.stringify(trx)}`)
    console.log(`register module receipt: ${JSON.stringify(receipt)}`)
  })
};
module.exports.tags = ['Modicum'];