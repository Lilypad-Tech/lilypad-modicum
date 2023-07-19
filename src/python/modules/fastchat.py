
import json

def _fastchat(params: str):
    cmd = ["python3", "main.py"]
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
                "Entrypoint": cmd,
                "Image": "xqua/carpai-demo-repo:v0.6",
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
            "inputs": [
                {
                    "CID": params,
                    "Name": "prompt_template_input",
                    "StorageSource": "IPFS",
                    "path": "/prompt_template.json",

                },
            ],
            "outputs": [
                {
                    "Name": "output",
                    "StorageSource": "IPFS",
                    "path": "/output"
                }
            ]
        }
    }

if __name__ == "__main__":
    print(_fastchat('QmcPjQwVcJiFge3yNjVL2NoZsTQ3GBpXAZe21S2Ncg16Gt'))
