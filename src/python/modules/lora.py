import json

def _lora(params: str):
    params = json.loads(params)
    if not isinstance(params, dict):
        raise Exception(
            "Please set params to a dict like "+
            "{'mode': 'training', 'seed': 42, 'input_cid': 'Qm...'} "+
            "(where input cid has images in), or "+
            "{'mode': 'inference', 'prompt': 'an astronaut in the style of <s1><s2>', "+
            "seed: 11, 'lora_cid': 'Qm...'} "+
            "where lora_cid is the output cid of the above step")

    # TODO: update following
    mode = params.get("mode", "inference")
    if mode == "inference":
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
                        "python3",
                        "inference.py",
                    ],
                    "Image": "quay.io/lukemarsden/sdxl:v0.9-lilypad1",
                    "EnvironmentVariables": [
                        f"PROMPT={params.get('prompt', 'question mark floating in space')}",
                        f"RANDOM_SEED={params.get('seed', 42)}",
                        f"OUTPUT_DIR=/outputs/",
                        "HF_HUB_OFFLINE=1",
                    ]
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
    elif mode == "training":
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
                        "python3",
                        "inference.py",
                    ],
                    "Image": "quay.io/lukemarsden/sdxl:v0.9-lilypad1",
                    "EnvironmentVariables": [
                        f"PROMPT={params.get('prompt', 'question mark floating in space')}",
                        f"RANDOM_SEED={params.get('seed', 42)}",
                        f"OUTPUT_DIR=/outputs/",
                        "HF_HUB_OFFLINE=1",
                    ]
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
    else:
        raise Exception(f"unknown mode {mode}")