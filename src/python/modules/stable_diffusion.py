def _stable_diffusion(params: str):
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
            "Docker": {
                "Entrypoint": [
                    "echo",
                    params,
                ],
                "Image": "ubuntu:22.04"
            },
            "Engine": "Docker",
            "Language": {
                "JobContext": {}
            },
            "Network": {
                "Type": "None"
            },
            "PublisherSpec": {
                "Type": "Estuary"
            },
            "Resources": {
                "GPU": "1"
            },
            "Timeout": 1800,
            "Verifier": "Noop",
            "Wasm": {
                "EntryModule": {}
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

# denoted in eth
_stable_diffusion.price = 91