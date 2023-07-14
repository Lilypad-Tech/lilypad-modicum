const hre = require('hardhat')

const {
  getWallet,
} = require('../accounts')

const {
  ethers,
  deployments,
} = hre

const {
  transfer,
} = require('../utils')

async function main() {
  const deployment = await deployments.get('Modicum')
  const ModicumFactory = await ethers.getContractFactory("Modicum")
  const modicumContract = ModicumFactory.attach(deployment.address)
  const wallet = getWallet('resource_provider')
  const signer = wallet.connect(hre.ethers.provider)
  const trx1 = await modicumContract
    .connect(signer)
    .registerResourceProvider(1, 0)
  const receipt1 = await trx1.wait()
  const trx2 = await modicumContract
    .connect(signer)
    .postResOffer(0, 0, 0, 0, 0, 0, 0, 0, 0)
  const receipt2 = await trx2.wait()
  console.log(`trx2: ${JSON.stringify(trx1)}`)
  console.log(`receipt2: ${JSON.stringify(receipt1)}`)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
