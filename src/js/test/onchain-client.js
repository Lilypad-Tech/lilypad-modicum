const hre = require('hardhat')
const chai = require('chai')
const chaiAsPromised = require('chai-as-promised')
const ethereumWaffle = require('ethereum-waffle')

chai.use(ethereumWaffle.solidity)
chai.use(chaiAsPromised)
const { expect } = chai


describe("Modicum", async () => {

  let modicumContract
  let examplesContract
  let adminAccount

  const deployModicum = async () => {
    const modicumFactory = (await ethers.getContractFactory(
      "Modicum",
      {
        signer: adminAccount,
      }
    ))
    modicumContract = await modicumFactory.deploy()
    await modicumContract.deployed()
  }

  const deployExamples = async (modicumAddress) => {
    const examplesFactory = (await ethers.getContractFactory(
      "ExamplesClient",
      {
        signer: adminAccount,
      }
    ))
    examplesContract = await examplesFactory.deploy(modicumAddress)
    await examplesContract.deployed()
  }

  const deployContracts = async () => {
    await deployModicum()
    await deployExamples(modicumContract.address)
    console.log(`modicumContract: ${modicumContract.address}`)
    console.log(`examplesContract: ${examplesContract.address}`)
  }

  
  context('contract', () => {
    beforeEach(async () => {
      [
        adminAccount,
      ] = await ethers.getSigners()
      await deployContracts()
    })

    describe('constructor', () => {
      it('deploys', async () => {
        const template = `apples"oranges`
        const params = `Here's a "thing"`

        const jobSpec = await examplesContract.getModuleSpec(template, params)

        console.log('--------------------------------------------')
        console.log(jobSpec)

        const parsedJobSpec = JSON.parse(jobSpec)

        expect(parsedJobSpec.template).to.equal(template)
        expect(parsedJobSpec.params).to.equal(params)
      })

      it('runs a job', async () => {
        const jobID = await examplesContract.runCowsay("holy cow")

        console.log('--------------------------------------------')
        console.log(jobID)
      })
    })
  })
  
})