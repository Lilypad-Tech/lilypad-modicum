pragma solidity ^0.4.25;
// import "hardhat/console.sol";

contract ExamplesClient {

  address public _contractAddress;

  constructor (address contractAddress) public {
    require(contractAddress != address(0), "ExamplesClient: contract cannot be zero address");
    _contractAddress = contractAddress;
  }

  function runCowsay(/*string sayWhat*/) public pure returns (uint256) {
    return 0;
  }

  function runStablediffsion(/*string prompt*/) public pure returns (uint256) {

    return 0;
  }

// {
//           "template": template,
//           "params": params
//         }
  function getJobSpec(string template, string params) public pure returns (string) {
    string memory saneTemplate = stringReplaceAll(template, "\"", "\\\"");
    string memory saneParams = stringReplaceAll(params, "\"", "\\\"");
    return string(abi.encodePacked("{\"template\": \"", saneTemplate, "\", \"params\": \"", saneParams, "\"}"));
  }

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
