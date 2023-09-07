import yaml

def _duckdb(params: str):
    if params.startswith("{"):
        params = yaml.safe_load(params)
    else:
        raise Exception("Please set params to yaml like {'query': 'SELECT...', 'inputs_cid': 'Qm...'}")

    return {
        "APIVersion": "V1beta1",
        "Metadata": {
            "CreatedAt": "0001-01-01T00:00:00Z",
            "Requester": {}
        },
        "Spec": {
            "Engine": "Docker",
            "Verifier": "Noop",
            "Publisher": "Estuary",
            "PublisherSpec": {
                "Type": "Estuary"
            },
            "Docker": {
                "Image": "31z4/bacalhau-duckdb:0.0.1",
                "Entrypoint": [
                    "./duckdb",
                    "-init",
                    "/init.sql",
                    "-echo",
                    "-s",
                    params["query"]
                ],
            },
            "Language": {
                "JobContext": {}
            },
            "Wasm": {
                "EntryModule": {}
            },
            "Resources": {
                "GPU": ""
            },
            "Network": {
                "Type": "None"
            },
            "Timeout": 1800,
            "inputs": [
                {
                    "StorageSource": "IPFS",
                    "Name": "inputs",
                    "CID": params["inputs_cid"],
                    "path": "/inputs",
                }
            ],
            "outputs": [
                {
                    "StorageSource": "IPFS",
                    "Name": "outputs",
                    "path": "/outputs"
                }
            ],
            "Deal": {
                "Concurrency": 1
            },
        },
    }
