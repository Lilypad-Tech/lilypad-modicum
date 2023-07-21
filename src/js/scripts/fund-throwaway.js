const Wallet = require('ethereumjs-wallet').default
const hre = require('hardhat')

const {
  FUND_THROWAWAY_AMOUNT,
  getAccount,
} = require('../accounts')

async function main() {
  const wallet = Wallet.generate()
  const fromAccount = getAccount('admin')
  const signer = new hre.ethers.Wallet(fromAccount.privateKey, hre.ethers.provider)
  const tx = await signer.sendTransaction({
    to: wallet.getAddressString(),
    value: FUND_THROWAWAY_AMOUNT,
  })
  await tx.wait()

  console.log(`Moved ${FUND_THROWAWAY_AMOUNT} from admin (${fromAccount.address}) to ${wallet.getAddressString()}: ${tx.hash}
  
address: ${wallet.getAddressString()}
privateKey: ${wallet.getPrivateKeyString()}
`)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
