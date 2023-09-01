// SPDX-License-Identifier: GPLv3
pragma solidity ^0.8.6;

interface ModicumContract {
  function runModuleWithDefaultMediators(string calldata name, string calldata params) external payable returns (uint256);
}

// Payment is 2 lilETH for all jobs currently
// got to testnet.lilypadnetwork.org to fund your wallet
contract ExampleClient {
  address public _contractAddress;
  ModicumContract remoteContractInstance;

  uint256 public lilypadFee = 2;

  struct Result {
      uint256 jobID;
      string cid;
      string httpString;
  }

  Result[] public results;

  event ReceivedJobResults(uint256 jobID, string cid);

  
