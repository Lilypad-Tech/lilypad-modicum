pragma solidity ^0.4.25;
// import "hardhat/console.sol";

interface ModicumContract {
  function runModule(string moduleSpec) external payable returns (uint256);
}

contract ExamplesClient {

  address public _contractAddress;
  ModicumContract remoteContractInstance;

  constructor (address contractAddress) public {
    require(contractAddress != address(0), "ExamplesClient: contract cannot be zero address");
    // NOTE: this is an example - so there are lots of "require" statements missing
    // e.g. we should check the address that is passed in is a valid contract address
    _contractAddress = contractAddress;
    remoteContractInstance = ModicumContract(contractAddress);
  }

  function runCowsay(string sayWhat) public returns (uint256) {
    return runModuleSpec(getModuleSpec("cowsay:v0.0.1", sayWhat));
  }

  function runStablediffsion(string prompt) public returns (uint256) {
    return runModuleSpec(getModuleSpec("stable_diffusion:v0.0.1", prompt));
  }

  function getModuleSpec(string template, string params) public pure returns (string) {
    string memory saneTemplate = stringReplaceAll(template, "\"", "\\\"");
    string memory saneParams = stringReplaceAll(params, "\"", "\\\"");
    return string(abi.encodePacked("{\"template\": \"", saneTemplate, "\", \"params\": \"", saneParams, "\"}"));
  }

  function runModuleSpec(string jobSpec) public returns (uint256) {
    return remoteContractInstance.runModule(jobSpec);
  }

  // function postJobResults(uint256 jobID, string cid) external {
    
  // }

  function stringReplaceAll(string memory _str, string memory _find, string memory _replace) private pure returns (string memory) {
    bytes memory str = bytes(_str);
    bytes memory find = bytes(_find);
    bytes memory replace = bytes(_replace);
    string memory result = "";

    for(uint i = 0; i < str.length; i++) {
      bool found = true;
      for(uint j = 0; j < find.length && found; j++) {
        if(i+j >= str.length || str[i+j] != find[j]) {
          found = false;
        }
      }
      if(found) {
        result = string(abi.encodePacked(result, replace));
        i += find.length - 1;
      } else {
        result = string(abi.encodePacked(result, string(abi.encodePacked(str[i]))));
      }
    }
    return result;
  }


}
