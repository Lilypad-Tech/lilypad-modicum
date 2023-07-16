module.exports = async ({getNamedAccounts, deployments}) => {
  const {deploy} = deployments
  const {admin} = await getNamedAccounts()
  const deploymentModicum = await deployments.get('Modicum')
  await deploy('NaiveExamplesClient', {
    from: admin,
    args: [deploymentModicum.address],
    log: true,
  });
  const deploymentExamples = await deployments.get('NaiveExamplesClient')
  console.log(`DEPLOYED NaiveExamplesClient: ${deploymentExamples.address}`)
};
module.exports.tags = ['NaiveExamplesClient'];