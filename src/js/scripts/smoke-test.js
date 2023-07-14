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
  const deploymentExamples = await deployments.get('NaiveExamplesClient')
  const ExamplesFactory = await ethers.getContractFactory("NaiveExamplesClient")
  const examplesContract = ExamplesFactory.attach(deploymentExamples.address)
  const walletExamples = getWallet('job_creator')
  const signerExamples = walletExamples.connect(hre.ethers.provider)
  const trx = await examplesContract
    .connect(signerExamples)
    .runCowsay('holy cow', {
      value: ethers.utils.parseEther("1"),
    })
  const receipt = await trx.wait()

  





  console.log(`trx2: ${JSON.stringify(trx2)}`)
  console.log(`receipt2: ${JSON.stringify(receipt2)}`)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
