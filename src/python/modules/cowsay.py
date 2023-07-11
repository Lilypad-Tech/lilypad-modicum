def _cowsay(params: str):
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
                    "/usr/games/cowsay",
                    params,
                ],
                "Image": "grycap/cowsay:latest"
            },
            "Engine": "Docker",
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
            "Verifier": "Noop"
        }
    }

# denoted in eth
_cowsay.price = 0.1