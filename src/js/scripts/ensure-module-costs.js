const hre = require('hardhat')
const bluebird = require('bluebird')

const {
  getWallet,
} = require('../accounts')

const {
  getContract,
} = require('../utils')

const {
  ethers,
} = hre

const MODULE_COSTS = {
  "stable_diffusion:v0.0.1": 4,
  "sdxl:v0.9-lilypad1": 4,
  "lora_training:v0.1.7-lilypad1": 50,
  "lora_inference:v0.1.7-lilypad1": 4,
  "cowsay:v0.0.1": 1,
  "fastchat:v0.0.1": 2,
  "filecoin_data_prep:v0.0.1": 100,
  "deterministic_wasm:v0.0.1": 2,
}

async function main() {
  const modicumContract = await getContract('Modicum')
  const wallet = getWallet('admin')
  const signer = wallet.connect(hre.ethers.provider)

  await bluebird.mapSeries(Object.keys(MODULE_COSTS), async (moduleName) => {
    const currentCost = await modicumContract.getModuleCost(moduleName)
    const MODULE_COST = ethers.utils.parseEther(MODULE_COSTS[moduleName].toString())
    const tx = await modicumContract
      .connect(signer)
      .setModuleCost(moduleName, MODULE_COST)
    await tx.wait()
    console.log('--------------------------------------------')
    console.log(`updated module: ${moduleName} from cost ${currentCost} to cost ${MODULE_COST}`)
    console.log(`tx: ${tx.hash}`)
  })
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})