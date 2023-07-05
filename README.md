## MODICUM demo

We need the following installed:

 * docker

In first pane:

```bash
./stack build
./stack hardhat
```

The smart contract is now deployed and the address is written to the JSON file living in `src/js/deployments/localhost/Modicum.json`

The command `./stack modicum` will run the modicum python process in a Docker container and will extract and inject the `CONTRACT_ADDRESS` environment variable into the container (by reading it fron the JSON file generated by the hardhat container).

```bash
./stack lilypad-modicum-process runAsSolver
```

```bash
./stack lilypad-modicum-process runAsMediator
```

```bash
./stack lilypad-node
```

To watch the logs from the node (which is multiple processes running inside one docker container):
```bash
./stack lilypad-logs
```

```bash
./stack lilypad-modicum-process runLilypadCLI --template stable_diffusion --params "hello"
```

## production node

We use the terraform scripts to run a single google cloud node.

### production geth

We are running geth in [developer mode](https://geth.ethereum.org/docs/developers/dapp-developer/dev-mode).

#### private key

Once we have started geth the first time - the `/data/geth/keystore` folder will have a single file inside.

Copy the contents of this file locally to `/tmp/bravo-geth/keystore.json` - also copy `/data/password.txt` to `/tmp/bravo-geth/password.txt`.

Then we use the node script to extract the private key of the account that has funds on the production node:

```bash
node src/js/scripts/extract-private-key-from-keystore.js --file /tmp/bravo-geth/keystore.json --password $(cat /tmp/bravo-geth/password.txt)
```

We then use this private key with hardhat to deploy the smart contract.