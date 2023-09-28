# Development

**NOTE: GPU development (and deployment) works best on Ubuntu 20.04 currently**

We need the following installed:

 * docker
 * jq
 * bash version 4.0.0 or higher (your default bash is likely outdated)

#### compile contract

The first thing we need to do is compile the smart contract so we have the ABI and can build that into the container:

```bash
(cd src/js && npm install && npx hardhat compile)
```

#### create addresses

Then we create a new address using:

```bash
node src/js/scripts/create-new-accounts.js > .env
source .env
```

#### run geth

In first pane:

```bash
./stack build
./stack geth
```

#### fund accounts

Now we need to fund all of our accounts:

```bash
./stack fund-admin
./stack fund-faucet
./stack fund-services
./stack balances
```

#### deloy contract

Then we can deploy the contract:

```bash
(cd src/js && npx hardhat deploy --network localgeth)
```

The smart contract is now deployed and the address is written to the JSON file living in `src/js/deployments/localgeth/Modicum.json`

#### run services

Each of these in a different window.

```bash
source .env
./stack solver && ./stack logs solver
```

```bash
source .env
./stack mediator && ./stack logs mediator
```

```bash
source .env
./stack resource-provider && ./stack logs resource-provider
```

```bash
source .env
./stack submitjob --template cowsay:v0.0.1 --params "hello"
```

NOTE: if you want a fresh installation - then:

```bash
./stack clean
```
