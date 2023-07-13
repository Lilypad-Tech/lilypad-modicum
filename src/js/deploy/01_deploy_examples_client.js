module.exports = async ({getNamedAccounts, deployments}) => {
  const {deploy} = deployments
  const {admin} = await getNamedAccounts()
  const deploymentModicum = await deployments.get('Modicum')
  await deploy('NaiveExamplesClient', {
    from: admin,
    args: [deploymentModicum.address],
    log: true,
  });
};
module.exports.tags = ['NaiveExamplesClient'];