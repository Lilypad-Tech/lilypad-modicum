module.exports = async ({getNamedAccounts, deployments}) => {
  const {deploy} = deployments
  const {admin} = await getNamedAccounts()
  const deploymentModicum = await deployments.get('Modicum')
  console.log('--------------------------------------------')
  console.log('--------------------------------------------')
  console.log('--------------------------------------------')
  console.log(`FETCHING MODICUM: ${deploymentModicum.address}`)
  await deploy('NaiveExamplesClient', {
    from: admin,
    args: [deploymentModicum.address],
    log: true,
  });
  const deploymentExamples = await deployments.get('NaiveExamplesClient')
  console.log(`DEPLOYED NaiveExamplesClient: ${deploymentExamples.address}`)
};
module.exports.tags = ['NaiveExamplesClient'];