const {
  getWallet,
} = require('../accounts')

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

  const trx = await modicumContract
    .connect(adminSigner)
    .setDefaultMediators([
      mediatorAccount.address,
    ])
  const receipt = await trx.wait()
  console.log(`add mediator trx: ${JSON.stringify(trx)}`)
  console.log(`add mediator receipt: ${JSON.stringify(receipt)}`)
};
module.exports.tags = ['Modicum'];