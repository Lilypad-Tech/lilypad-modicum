# Lilypad 🍃

This cloud is just someone else's computer.

![image](https://github.com/bacalhau-project/lilypad/assets/264658/d91dad9a-ca46-43d4-a94b-d33454efc7ae)

This guide shows you (amongst other things) how to make crypto with your gaming GPU by running stable diffusion jobs for someone else. (caveat, today it is just worthless test crypto, but one day soon it will be real crypto!)


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
* Account details - then we'll **Show private key**

<img src="https://github.com/bacalhau-project/lilypad/assets/264658/4e947efb-888c-4c85-9990-ab01cb889516" width="300">

* Show private key
* Enter your metamask password
* Copy private key for account

Open a terminal on macOS, Linux or WSL2, and type:
```
export PRIVATE_KEY=<the private key you copied>
```

TODO: faucet

Now let's run a job!

## Hello (cow) world example

Requires:
* [Docker](https://docs.docker.com/engine/install/)


Install `lilypad` CLI (shell wrapper, works on Linux, macOS and WSL2)
```
curl -sSL -O https://bit.ly/get-lilypad && sudo install get-lilypad /usr/local/bin/lilypad
```

### run a job
Run cowsay via the BLOCKCHAIN
```
lilypad run --template cowsay:v0.0.1 --params "hello lilypad"
```

### run a node
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



