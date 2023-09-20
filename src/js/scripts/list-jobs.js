const hre = require('hardhat')
const bluebird = require('bluebird')

const {
  ethers,
  deployments,
} = hre

async function main() {
  const deployment = await deployments.get('Modicum')
  const Factory = await ethers.getContractFactory('Modicum')
  const contract = Factory.attach(deployment.address)

  const filter = contract.filters.JobOfferPostedPartTwo()
  const events = await contract.queryFilter(filter, 0, 'latest');

  const eventsPerAddress = {}
  const eventsPerModule = {}
  let totalJobs = 0

  events.forEach(ev => {
    if(!eventsPerAddress[ev.args.addr]) {
      eventsPerAddress[ev.args.addr] = []
    }
    eventsPerAddress[ev.args.addr].push(ev)
    totalJobs++
    try {
      const args = JSON.parse(ev.args.extras.replace(/\n/g, ""))
      const currentTotal = eventsPerModule[args.template] || 0
      eventsPerModule[args.template] = currentTotal + 1
    } catch(e) {
      console.log('--------------------------------------------')
      console.log(ev.args.extras)
    }
  })

  const uniqueUsers = Object.keys(eventsPerAddress).length

  console.log(`Total jobs: ${totalJobs}`)
  console.log(`Unique users: ${uniqueUsers}`)
  console.dir(eventsPerModule)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
