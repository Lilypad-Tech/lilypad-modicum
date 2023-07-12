# Lilypad 🍃

This cloud is just someone else's computer.

![image](https://github.com/bacalhau-project/lilypad/assets/264658/d91dad9a-ca46-43d4-a94b-d33454efc7ae)

This guide shows you (amongst other things) how to make crypto with your gaming GPU by running stable diffusion jobs for someone else. (caveat, today it is just worthless test crypto, but one day soon it will be real crypto!)


## Hello (cow) world example

Requires:
* [Docker](https://docs.docker.com/engine/install/)

TODO: set `PRIVATE_KEY`

Install `lilypad` CLI (shell wrapper, works on Linux, macOS and WSL2)
```
curl -sSL -O https://bit.ly/get-lilypad && sudo install get-lilypad /usr/local/bin/lilypad
```

Run cowsay via the BLOCKCHAIN
```
lilypad run --template cowsay --params "oh hello my dear cow"
```

TODO: How to run a node
```
sudo lilypad serve
```

# Development

We need the following installed:

 * docker
 * jq

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
exit
```

Make sure we have the `.env` setup (see above)

Now we run the following commands:

```bash
source .env
(cd src/js && npx hardhat compile)
```

### production deploy

# usage

## cowsay

```
./stack submitjob --template cowsay:v0.0.1 --params "i am a silly cow"
```

## stable diffusion (requires GPU)

```
./stack submitjob --template stable_diffusion:v0.0.1 --params "blue frog"
```

TODO:
* fine tuning stable diffusion with LoRA
* inference on a fine-tuned LoRA
* t2i sketch, depth & pose
* controlnet
* support some subset of https://platform.stability.ai/docs/features

## filecoin data prep

```
./stack submitjob --template filecoin_data_prep:v0.0.1 \
	--params '{"s3_bucket": "noaa-goes16", \
	           "s3_key": "ABI-L1b-RadC/2000/001/12/OR_ABI-L1b-RadC-M3C01*"}'
```

* TODO: read results from http rather than ipfs for high performance

## arbitrary wasm (run in a deterministic env)

* TODO: the following seems to be a `csv2parquet` program that requires a CSV as input - need to also provide a CSV as input! (but it runs, giving the error message rn)

```
./stack submitjob --template deterministic_wasm:v0.0.1 \
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





