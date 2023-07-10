## MODICUM demo

### development

We need the following installed:

 * docker
 * jq

NOTE: if you want a fresh installation - then:

```bash
sudo rm -rf /tmp/geth
rm -rf src/js/deployments/localgeth
```

#### compile contract

The first thing we need to do is compile the smart contract so we have the ABI and can build that into the container:

```bash
cd src/js
npm install
npx hardhat compile
```

#### admin address

Then we create a new address using:

```bash
cd src/js
node scripts/create-new-account.js
```

Create a `src/js/.env` file like this:

```
ADMIN_ADDRESS=...
ADMIN_PRIVATE_KEY=...
```

Copy the values into the `src/js/.env` file.

#### run geth

In first pane:

```bash
./stack build
./stack geth
```

We then need to move some funds to our admin wallet address:

```bash
source src/js/.env
./stack geth-fund $ADMIN_ADDRESS
./stack geth-balance $ADMIN_ADDRESS
```

#### deloy contract

Then we can deploy the contract:

```bash
cd src/js
npx hardhat deploy --network localgeth
```

The smart contract is now deployed and the address is written to the JSON file living in `src/js/deployments/localgeth/Modicum.json`

#### run services

```bash
./stack solver && ./stack logs solver
```

```bash
./stack mediator && ./stack logs mediator
```

```bash
./stack resource-provider && ./stack logs resource-provider
```

```bash
./stack submitjob --template cowsay:v0.0.1 --params "hello"
```

### production initial node setup

We use the terraform scripts to run a single google cloud node.

```bash
gcloud auth application-default login
gcloud config set project bacalhau-production
cd ops/testnet
terraform init
terraform apply
gcloud compute instances list
gcloud compute ssh bravo-testnet-vm-0 --zone us-central1-a
sudo docker ps -a
exit
```

We are running geth in [developer mode](https://geth.ethereum.org/docs/developers/dapp-developer/dev-mode).

This is how to run geth on the vm:

```bash
cd ops/testnet
bash deploy.sh run-geth
```

#### root account

The `--dev` flag we pass to geth means we have a single node eth node without any peers, will mine blocks as soon as transactions are in the mempool and will pre-fund a single, unlocked account.  We have mounted the geth data dir onto the google disk mounted to the vm.

The root account is unlocked - to prevent someone rocking up and draining that account - we move all the funds to another account which we have an offline private key for.

NOTE: this is a record of what was done - it doesn't need to be done again

First we generate an account address and private key:

```bash
cd src/js
node scripts/create-new-account.js
```

NOTE: this is just generating a new address and private key - it's not actually doing anything on the blockchain

We then add these values to the `src/js/.env` file - which hardhat-deploy uses to deploy the smart contract.

```
ADMIN_ADDRESS=0x85eae6e6a316eab840ac82d83684bae8e369e64d
ADMIN_PRIVATE_KEY=...
```

Now - we need to transfer funds from the root unlocked account to our admin address:

First we get into the geth container on the vm:

```bash
gcloud compute ssh bravo-testnet-vm-0 --zone us-central1-a
docker exec -ti geth sh
```

Then we run the commands to transfer funds from the root account to our admin address:

```bash
geth --exec 'eth.coinbase' attach /data/geth/geth.ipc
geth --exec 'eth.sendTransaction({from: eth.coinbase, to: "0x85eae6e6a316eab840ac82d83684bae8e369e64d", value: web3.toWei(10000000000000, "ether")})' attach /data/geth/geth.ipc
geth --exec 'eth.getBalance("0x85eae6e6a316eab840ac82d83684bae8e369e64d")/1e18' attach /data/geth/geth.ipc
```

Now we have a private key for a locked account with funds - this means we can deploy the contract from this address and no-one can then use the fact the account is unlocked to drain the funds or mess with the contract.

#### deploy contract

Now we have the `.env` file with the `ADMIN_PRIVATE_KEY` for our address that has funds - we can deploy the contract using hardhat:

```bash
cd src/js
npx hardhat compile
# this will deploy to the local geth
npx hardhat deploy --network localgeth
# this will deploy to the production geth
npx hardhat deploy --network production
```

# usage

Run this first (for now):
```
alias lilypad-run='docker run -ti --rm --net host --entrypoint "/usr/local/bin/modicum" -v /var/run/docker.sock:/var/run/docker.sock -v ./src/python:/app -e CONTRACT_ADDRESS=$(cat src/js/deployments/localhost/Modicum.json | jq -r .address) lilypad-docker-python runLilypadCLI'
```

## cowsay

```
lilypad-run --template cowsay:v0.0.1 --params "i am a silly cow"
```

## stable diffusion (requires GPU)

```
lilypad-run --template stable_diffusion:v0.0.1 --params "blue frog"
```

TODO:
* fine tuning stable diffusion with LoRA
* inference on a fine-tuned LoRA
* t2i sketch, depth & pose
* controlnet
* support some subset of https://platform.stability.ai/docs/features

## filecoin data prep

```
lilypad-run --template filecoin_data_prep:v0.0.1 \
	--params '{"s3_bucket": "noaa-goes16", \
	           "s3_key": "ABI-L1b-RadC/2000/001/12/OR_ABI-L1b-RadC-M3C01*"}'
```

* TODO: read results from http rather than ipfs for high performance

## arbitrary wasm (run in a deterministic env)

* TODO: the following seems to be a `csv2parquet` program that requires a CSV as input - need to also provide a CSV as input! (but it runs, giving the error message rn)

```
lilypad-run --template deterministic_wasm:v0.0.1 \
	--params '{"wasm_cid": "Qmajb9T3jBdMSp7xh2JruNrqg3hniCnM6EUVsBocARPJRQ", \
	           "wasm_entrypoint": "_start"}'
```


#### production

Step 0 = build and push images

```bash
./stack build
./stack push-images
```

Step 1 = run geth in production.

Step 2 = transfer funds to admin account.

Step 3 = deploy contract using hardhat `production` network

Step 4 = export variables

These variables are exported on the node

```bash
export TRIM=production
export CONTRACT_ADDRESS=0x219F074D9b14410868105420eEEa9Ba768a7aAE1
export VERSION=...
```

Step 4 = run solver and mediator services

^ all of the above is done using the `stack` script on the production node.

Step 5 = run resource-provider on a separate node

NOTE: you need to use `export TRIM=production-client` on the resource-provider node

```bash
export TRIM=production-client
./stack resource-provider
```

Step 6 = submit jobs

NOTE: you need to use `export TRIM=production-client` on the client node

```bash
export TRIM=production-client
./stack submitjob --template cowsay:v0.0.1 --params "hello"
```





