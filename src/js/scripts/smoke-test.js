const hre = require('hardhat')

const {
  getWallet,
} = require('../accounts')

const {
  getContract,
} = require('../utils')

async function main() {
  const examplesContract = await getContract('NaiveExamplesClient')
  const modicumContract = await getContract('Modicum')
  const walletExamples = getWallet('job_creator')
  const signerExamples = walletExamples.connect(hre.ethers.provider)
  const price = await modicumContract.getModuleCost('cowsay:v0.0.1')
  const trx = await examplesContract
    .connect(signerExamples)
    .runCowsay(`holy cow this is a job ran at timestamp: ${new Date().getTime()}`, {
      value: price,
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
