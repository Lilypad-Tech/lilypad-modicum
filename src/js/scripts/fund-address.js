const {
  getAccount,
} = require('../accounts')

async function main() {
  if(!process.env.ADDRESS) {
    console.error(`no ADDRESS env found`)
    process.exit(1)
  }
  if(!process.env.AMOUNT) {
    console.error(`no AMOUNT env found`)
    process.exit(1)
  }
  const fromAccount = getAccount('admin')
  const signer = new hre.ethers.Wallet(fromAccount.privateKey, hre.ethers.provider)

  const tx = await signer.sendTransaction({
    to: process.env.ADDRESS,
    value: ethers.utils.parseEther(process.env.AMOUNT),
  })
  await tx.wait()

  console.log(`Moved ${process.env.AMOUNT} from admin (${fromAccount.address}) to ${process.env.ADDRESS} ${tx.hash}.`)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
