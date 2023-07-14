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
    .runCowsay(`holy cow this is a job ran at timestamp: ${new Date().getTime()}`, {
      value: ethers.utils.parseEther("1"),
    })
  await trx.wait()
  examplesContract.on('ReceivedJobResults', (jobID, cid) => {
    console.log(`jobID: ${jobID}`)
    console.log(`results CID: ${cid}`)
    console.log(`https://ipfs.io/ipfs/${cid}`)
    process.exit(0)
  })
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
