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

  const filter = contract.filters.JobOfferPostedPartTwo()
  const events = await contract.queryFilter(filter, 0, 'latest');

  const eventsPerAddress = {}
  const eventsPerModule = {}
  let totalJobs = 0
  const csvData = []

  await bluebird.mapSeries(events, async (ev) => {
    const block = await ev.getBlock()
    if(!eventsPerAddress[ev.args.addr]) {
      eventsPerAddress[ev.args.addr] = []
    }
    eventsPerAddress[ev.args.addr].push(ev)
    totalJobs++
    
    const args = JSON.parse(ev.args.extras.replace(/\n/g, ""))
    const currentTotal = eventsPerModule[args.template] || 0
    eventsPerModule[args.template] = currentTotal + 1

    csvData.push({
      address: ev.args.addr,
      module: args.template,
      timestamp: new Date(block.timestamp * 1000).toISOString(),
    })

    console.error(`Processed ${totalJobs} / ${events.length} events.`)
  }, {
    concurrency: 10,
  })
  
  const csv = Papa.unparse(csvData)
  console.log(csv)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
