def _scorepoc():
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
                "Image": "solityresearch/poc-testv5@sha256:82ebb534e0495d4c82053c7b974083c3c6e20060d7309995982e77229ecc60c0"
            },
            "Engine": "Docker",
            "Network": {
                "Type": "None"
            },
            "Publisher": "Estuary",
            "PublisherSpec": {
                "Type": "Estuary"
            },
            "Resources": {
                "GPU": ""
            },
            "Timeout": 1800,
            "Verifier": "Noop",
            "Language": {
                "JobContext": {}
            },
            "Wasm": {
                "EntryModule": {}
            },
            "inputs": [
                {
                    "StorageSource": "URLDownload",
                    "Name": "https://pods.dev-solity.net/test-decentralized/social-data",
                    "URL": "https://pods.dev-solity.net/test-decentralized/social-data",
                    "path": "/inputs"
                }
            ],
            "outputs": [
                {
                    "StorageSource": "IPFS",
                    "Name": "outputs",
                    "path": "/outputs"
                }
            ]
        }
    }