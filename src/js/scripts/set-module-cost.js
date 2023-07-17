const hre = require('hardhat')

const {
  getWallet,
} = require('../accounts')

const {
  getContract,
} = require('../utils')

async function main() {
  // example of setting price of sdxl:v0.9-lilypad1 to 2 ETH
  const examplesContract = await getContract('NaiveExamplesClient')
  const modicumContract = await getContract('Modicum')
  const wallet = getWallet('admin')
  const signer = wallet.connect(hre.ethers.provider)
  const JOB_COST = ethers.utils.parseEther("2")
  const price = await modicumContract.setModuleCost('sdxl:v0.9-lilypad1', JOB_COST)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});