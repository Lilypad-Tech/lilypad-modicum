module.exports = async ({getNamedAccounts, deployments}) => {
  const {deploy} = deployments
  const {admin} = await getNamedAccounts()
  await deploy('Modicum', {
    from: admin,
    args: [],
    log: true,
  });
  const deploymentModicum = await deployments.get('Modicum')
  console.log('--------------------------------------------')
  console.log('--------------------------------------------')
  console.log('--------------------------------------------')
  console.log(`DEPLOYED MODICUM: ${deploymentModicum.address}`)
};
module.exports.tags = ['Modicum'];