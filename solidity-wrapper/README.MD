Solidity Wrapper creates a client with an existing solidity code to listen for events and call functions.

***Usage***

`main.py <src> <dst>`

  **src**         Path to Solidity source file
  
  **dst**         Path to output directory
  
in the output directory, `Contract.py` should be present

***Dependencies***
You should have `antlr4-python3-runtime` available in your virtualenv or pip global packages.


***Makefile***

To install dependencies: `make setupWrapper`

to create the wrapper: `make wrap` 