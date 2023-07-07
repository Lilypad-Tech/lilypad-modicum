#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

export IPFS_ID_FILE=${IPFS_ID_FILE:="/root/.ipfs_id"}

# keeping looping until the /root/.ipfs_id file appears
# if it is not there - wait 1 second to avoid thrash looping
while [ ! -f $IPFS_ID_FILE ]; do
  echo "file $IPFS_ID_FILE does not exist yet"
  sleep 1
  exit 1
done
 
IPFS_ID=$(cat $IPFS_ID_FILE | tr -d '[:space:]')
IPFS_ADDRESS="/ip4/127.0.0.1/tcp/5001/p2p/${IPFS_ID}"

bacalhau serve \
  --node-type compute,requester \
  --ipfs-connect "${IPFS_ADDRESS}" \
  --private-internal-ipfs=false