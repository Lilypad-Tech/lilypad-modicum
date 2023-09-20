const hre = require('hardhat')
const bluebird = require('bluebird')
const Papa = require('papaparse');

const {
  ethers,
  deployments,
} = hre

async function main() {
  const deployment = await deployments.get('Modicum')
  const Factory = await ethers.getContractFactory('Modicum')
  const contract = Factory.attach(deployment.address)

  const filter = contract.filters.ResourceOfferPosted()
  const events = await contract.queryFilter(filter, 0, 'latest');

  const eventsPerAddress = {}
  
  events.forEach((ev) => {
    if(!eventsPerAddress[ev.args.addr]) {
      eventsPerAddress[ev.args.addr] = []
    }
    eventsPerAddress[ev.args.addr].push(ev)
  })
  
  console.log(`Total resource providers: ${Object.keys(eventsPerAddress).length}`)
  console.log(`Total resource offers: ${events.length}`)


  Object.keys(eventsPerAddress).forEach(address => {
    console.log(`Address: ${address} ${eventsPerAddress[address].length} offers`)
  })
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
