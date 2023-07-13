// SPDX-License-Identifier: GPLv3
pragma solidity ^0.8.6;

interface ModicumContract {
  function runModuleWithDefaultMediators(string calldata name, string calldata params) external payable returns (uint256);
}

contract ExamplesClient {
  address public _contractAddress;
  ModicumContract remoteContractInstance;

  constructor (address contractAddress) {
    require(contractAddress != address(0), "ExamplesClient: contract cannot be zero address");
    _contractAddress = contractAddress;
    remoteContractInstance = ModicumContract(contractAddress);
  }

  function runCowsay(string calldata sayWhat) public returns (uint256) {
    return remoteContractInstance.runModuleWithDefaultMediators("cowsay:v0.0.1", sayWhat);
  }

  function runStablediffusion(string calldata prompt) public returns (uint256) {
    return remoteContractInstance.runModuleWithDefaultMediators("stable_diffusion:v0.0.1", prompt);
  }
}
