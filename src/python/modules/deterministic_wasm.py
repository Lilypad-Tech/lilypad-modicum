def _deterministic_wasm(params: dict):
    """
    params of form:
        {"wasm_cid": "a1b2",
         "wasm_entrypoint": "_start",
        }
    """
    # TODO: support input parameters as CIDs
    return {
        "APIVersion": "V1beta1",
        "Metadata": {
            "CreatedAt": "0001-01-01T00:00:00Z",
            "Requester": {}
        },
        "Spec": {
            "Deal": {
                "Concurrency": 1
            },
            "Engine": "Wasm",
            "Network": {
                "Type": "None"
            },
            "PublisherSpec": {
                "Type": "Estuary"
            },
            "Resources": {
                "GPU": ""
            },
            "Timeout": 1800,
            "Verifier": "Noop",
            "Wasm": {
                "EntryModule": {
                    "CID": params["wasm_cid"],
                    "StorageSource": "IPFS",
                },
                "EntryPoint": params["wasm_entrypoint"],
            },
            "outputs": [
                {
                    "Name": "outputs",
                    "StorageSource": "IPFS",
                    "path": "/outputs"
                }
            ]
        }
    }
