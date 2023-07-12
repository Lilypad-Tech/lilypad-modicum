const {
  FUND_FAUCET_AMOUNT,
} = require('../accounts')

const {
  transfer,
} = require('../utils')

async function main() {
  await transfer('admin', 'faucet', FUND_FAUCET_AMOUNT)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
