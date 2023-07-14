// SPDX-License-Identifier: GPLv3
pragma solidity ^0.8.6;

interface ModicumContract {
  function runModuleWithDefaultMediators(string calldata name, string calldata params) external payable returns (uint256);
}

contract NaiveExamplesClient {
  address public _contractAddress;
  ModicumContract remoteContractInstance;

  event ReceivedJobResults(uint256 jobID, string cid);

  constructor (address contractAddress) {
    require(contractAddress != address(0), "NaiveExamplesClient: contract cannot be zero address");
    _contractAddress = contractAddress;
    remoteContractInstance = ModicumContract(contractAddress);
  }

  function runCowsay(string memory sayWhat) public payable returns (uint256) {
    return runModule("cowsay:v0.0.1", sayWhat);
  }

  function runStablediffusion(string memory prompt) public payable returns (uint256) {
    return runModule("stable_diffusion:v0.0.1", prompt);
  }

  function runModule(string memory name, string memory params) public payable returns (uint256) {
    return remoteContractInstance.runModuleWithDefaultMediators{value: msg.value}(name, params);
  }

  function receiveJobResults(uint256 jobID, string calldata cid) public {
    emit ReceivedJobResults(jobID, cid);
  }
}
