# MODiCuM

## How to install and run:

### Step 1: Docker

Install docker as instructed in [here](https://docs.docker.com/install/linux/docker-ce/ubuntu/).

### Step 2: Blockchain

* Install golang: `apt install golang-1.7-go` or `wget https://storage.googleapis.com/golang/go1.7.1.linux-amd64.tar.gz`
* Download geth client 1.7.0 from `wget https://github.com/ethereum/go-ethereum/archive/v1.7.0.tar.gz`
* unzip and make
* in the bin folder add `genesis-data.json` and `password.txt`
(`password.txt` is your desired password for the accounts)
* init blockchain `./geth --datadir eth/  init genesis-data.json`
* create the first account on the block chain: `./geth account new --password password.txt --datadir eth/`
* start blockchain 
```bash
./geth --datadir eth/ --rpc --rpcport 10000 --rpcaddr 127.0.0.1 --nodiscover --rpcapi 'eth,web3,admin,miner,net,db' --password password.txt --unlock 0 --networkid 15 --mine --targetgaslimit 200000000000000000 console
```

It will need to run for some time so that there is ether in the wallet. And some of that ether will need to be transferred to the other accounts.
Some useful commands that can be used from the console that was started with the above commands are:

* current gas limit : `eth.getBlock("latest").gasLimit`
* ether in account 8 : `web3.fromWei(eth.getBalance(eth.accounts[8]), "ether")`
* send gas from account 0 to account 1 : `eth.sendTransaction({from:eth.accounts[0], to:eth.accounts[1], value: web3.toWei(10000, "ether")})`



### Step 3: Run MODiCuM

Make sure you have Python3 and pip installed

* go to `src/python`
* install the modicum command with: `sudo pip3 install -e .`
* fix your `.env` file and replace `<>`s with correct path information.
* set $CONTRACTSRC in the location of the contract: `export CONTRACTSRC=../MODiCuM/src/solidity`
* create directory `../MODiCuM/src/solidity/output`
* compile the smart contract with:
```bash
sudo docker run -it --rm\
		--name solcTest \
		--mount type=bind,source="$(CONTRACTSRC)",target=/solidity/input \
		--mount type=bind,source="$(CONTRACTSRC)/output",target=/solidity/output \
		ethereum/solc:0.4.25 \
		--overwrite --bin --bin-runtime --ast --asm -o /solidity/output /solidity/input/Modicum.sol
```
* run sample components in the following order:
    1. `modicum runAsCM`
    2. `modicum runAsSolver`
    3. `modicum runAsMediator`
    4. `modicum startJCDaemon`
    5. `modicum startRPDaemon`

_**ContractManager**_ is the entity who deploys the contract in the blockchain. Further, he has the responsibility to share the contract's address with other parties and entities.

Then you can start sending self designated messages with `modicum` command like `modicum JCaddMediator` and `modicum postJob`.
Just try `modicum --help`

### Optional Step: Changing the Smart Contract

You can use the Solidity Wrapper to regenerate the wrapper class `ModicumContract.py` and `Enums.py` file.
