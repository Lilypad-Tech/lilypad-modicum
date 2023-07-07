#!/bin/bash
set -euo pipefail
IFS=$'\n\t'
set -x

export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export ZONE=${ZONE:="us-central1-a"}
export NAME=${NAME:="bravo-testnet-vm-0"}

function gSSH() {
    gcloud compute ssh --quiet --zone=$ZONE $NAME -- sudo $*
}

function gSCP() {
    gcloud compute scp --quiet --zone=$ZONE $1 $NAME:$2
}

function run-geth() {
  gSSH docker rm -f geth || true
  gSSH docker run -d \
    --name geth \
    --restart always \
    -p 8545:8545 \
    -v /data/geth:/data/geth \
    ethereum/client-go \
      --datadir /data/geth \
      --dev --http \
      --http.api web3,eth,net \
      --http.addr 0.0.0.0
}

eval "$@"