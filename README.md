# Lilypad 🍃

This cloud is just someone else's computer.

![image](https://github.com/bacalhau-project/lilypad/assets/264658/d91dad9a-ca46-43d4-a94b-d33454efc7ae)

Read the [docs](https://docs.lilypadnetwork.org)!


This guide shows you (amongst other things) how to:

* trigger jobs on other peoples' computers with just a metamask wallet and our CLI
* trigger the same jobs from a smart contract deployed to our testnet
* make crypto with your GPU by running Stable Diffusion fine-tuning & inference jobs for someone else.

> Caveat: today it is just worthless test crypto, but one day soon it will be real crypto!


## Get private key

Set up metamask with our Lalechuza testnet.

Click the down arrow on networks and click add network.

<img src="https://github.com/bacalhau-project/lilypad/assets/264658/9f4bd43e-aef1-4d7b-8441-082b0355298f" width="300">

The variables you need are:

* Network name: `Lilypad Lalechuza testnet`
* New RPC URL: `http://testnet.lilypadnetwork.org:8545`
* Chain ID: `1337`
* Currency symbol: `ETH`
* Block explorer URL: (leave blank)

Click save and click "switch to Lilypad Lalechuza testnet".

* Click the **down arrow** next to Account 1 on the top bar, **then** click the `...` next to Account 1 in the list
* Account details - then click **Show private key**

<img src="https://github.com/bacalhau-project/lilypad/assets/264658/4e947efb-888c-4c85-9990-ab01cb889516" width="300">

* Show private key
* Enter your metamask password
* Copy private key for account - **DO NOT COPY THE WALLET ADDRESS BY MISTAKE**

Open a terminal on macOS, Linux or WSL2, and type:
```
export PRIVATE_KEY=<the private key you copied>
```

Go get some funds from the faucet: [http://testnet.lilypadnetwork.org/](http://testnet.lilypadnetwork.org/)

Now let's run a job!

## Hello (cow) world example

Requires:
* [Docker](https://docs.docker.com/engine/install/)

Works on Linux, macOS and WSL2 (x86_64 and arm64)

Install `lilypad` CLI:
```
curl -sSL -O https://raw.githubusercontent.com/bacalhau-project/lilypad-modicum/main/lilypad && sudo install lilypad /usr/local/bin/lilypad
```

### run a job (x86_64 or arm64)
Run cowsay via the BLOCKCHAIN
```
export PRIVATE_KEY=<as above>
lilypad run --template cowsay:v0.0.1 --params "hello lilypad"
```
(ensure your user is in the docker group if necessary on your platform)

### run a node (x86_64 only)
To contribute your resources to the network and get paid
```
export PRIVATE_KEY=<as above>
sudo -E lilypad serve
```

# usage

## stable diffusion (requires GPU)

```
lilypad run --template stable_diffusion:v0.0.1 --params "blue frog"
```

TODO:
* fine tuning stable diffusion with LoRA
* inference on a fine-tuned LoRA
* t2i sketch, depth & pose
* controlnet
* support some subset of https://platform.stability.ai/docs/features

## filecoin data prep

```
lilypad run --template filecoin_data_prep:v0.0.1 \
	--params '{"s3_bucket": "noaa-goes16", \
	           "s3_key": "ABI-L1b-RadC/2000/001/12/OR_ABI-L1b-RadC-M3C01*"}'
```

* TODO: read results from http rather than ipfs for high performance

## arbitrary wasm (run in a deterministic env)

* TODO: the following seems to be a `csv2parquet` program that requires a CSV as input - need to also provide a CSV as input! (but it runs, giving the error message rn)

```
lilypad run --template deterministic_wasm:v0.0.1 \
	--params '{"wasm_cid": "Qmajb9T3jBdMSp7xh2JruNrqg3hniCnM6EUVsBocARPJRQ", \
	           "wasm_entrypoint": "_start"}'
```



