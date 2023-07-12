// deploy/00_deploy_my_contract.js
module.exports = async ({getNamedAccounts, deployments}) => {
  const {deploy} = deployments
  const {admin} = await getNamedAccounts()
  await deploy('Modicum', {
    from: admin,
    args: [],
    log: true,
  });
};
module.exports.tags = ['Modicum'];