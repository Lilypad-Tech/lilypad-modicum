const hre = require('hardhat')

const {
  getNamedAccounts,
  deployments,
} = hre

async function main() {
  const accounts = await hre.ethers.getSigners()
  for (const account of accounts) {
    const balance = await hre.ethers.provider.getBalance(account.address)
    console.log(`${account.address} = ${balance.toString()}`)
  }
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
