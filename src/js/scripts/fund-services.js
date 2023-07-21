const {
  FUND_SERVICE_AMOUNT,
} = require('../accounts')

const {
  transfer,
} = require('../utils')

async function main() {
  await transfer('admin', 'solver', FUND_SERVICE_AMOUNT)
  await transfer('admin', 'mediator', FUND_SERVICE_AMOUNT)
  await transfer('admin', 'resource_provider', FUND_SERVICE_AMOUNT)
  await transfer('admin', 'job_creator', FUND_SERVICE_AMOUNT)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
