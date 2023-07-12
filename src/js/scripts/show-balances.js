const hre = require('hardhat')

const {
  getNamedAccounts,
} = hre

async function main() {
  const {
    admin,
    faucet,
    solver,
    mediator,
    resource_provider,
    job_creator,
  } = await getNamedAccounts()

  const accounts = [
    ['admin', admin],
    ['faucet', faucet],
    ['solver', solver],
    ['mediator', mediator],
    ['resource_provider', resource_provider],
    ['job_creator', job_creator],
  ]

  for (const account of accounts) {
    const balance = await hre.ethers.provider.getBalance(account[1])
    console.log(`${account[0]} - ${account[1]} = ${ethers.utils.formatEther(balance)}`)
  }
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
