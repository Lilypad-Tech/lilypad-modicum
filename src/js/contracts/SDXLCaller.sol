// SPDX-License-Identifier: GPLv3
pragma solidity ^0.8.6;

// give it the ModicumContract interface 
// NB: this will be a separate import in future.
interface ModicumContract {
  function runModuleWithDefaultMediators(string calldata name, string calldata params) external payable returns (uint256);
}

contract SDXLCaller {
  address public contractAddress;
  ModicumContract remoteContractInstance;
  
  // See the latest result.
  uint256 public resultJobId;
  string public resultCID;

  // The Modicum contract address is found here: https://github.com/bacalhau-project/lilypad-modicum/blob/main/latest.txt
  // Current: 0x422F325AA109A3038BDCb7B03Dd0331A4aC2cD1a
  constructor(address _modicumContract) {
    require(_modicumContract != address(0), "Contract cannot be zero address");
    contractAddress = _modicumContract;
    //make a connection instance to the remote contract
    remoteContractInstance = ModicumContract(_modicumContract);
  } 

  /*
  * @notice Run the SDXL Module
  * @param prompt The input text prompt to generate the stable diffusion image from
  */
  function runSDXL(string memory prompt) public payable returns (uint256) {
    require(msg.value == 2 ether, "Payment of 2 Ether is required"); //all jobs are currently 2 lilETH
    return remoteContractInstance.runModuleWithDefaultMediators{value: msg.value}("sdxl:v0.9-lilypad1", prompt);
  }
  
  // This must be implemented in order to receive the job results back!
  function receiveJobResults(uint256 _jobID, string calldata _cid) public {
    resultJobId =_jobID;
    resultCID = _cid;
  }
  
}
