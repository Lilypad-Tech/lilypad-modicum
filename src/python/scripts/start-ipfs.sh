#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# this whole section is designed to idempotently initialize ipfs
# and write the node id to a file so it can be picked up by
# the bacalhau wrapper script
export IPFS_BINARY=${IPFS_BINARY:="/usr/local/bin/ipfs"}
export IPFS_CONFIG_FILE=${IPFS_CONFIG_FILE:="/root/.ipfs/config"}
export IPFS_ID_FILE=${IPFS_ID_FILE:="/root/.ipfs_id"}
if [[ ! -f "$IPFS_CONFIG_FILE" ]]; then
  $IPFS_BINARY init
fi
id=$(cat "$IPFS_CONFIG_FILE" | jq -r .Identity.PeerID)
echo -n "$id" > $IPFS_ID_FILE

# this is the main entrypoint for the container
$IPFS_BINARY daemon