import yaml

def _sdxl(params: str):
    if params.startswith("{"):
        params = yaml.safe_load(params)
    else:
        prompt = params
        params = {"prompt": prompt, "seed": 0}
    if not isinstance(params, dict):
        raise Exception("Please set params to a dict like {'prompt': 'astronaut riding a horse', 'seed': 42}")
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
                    "bash", "-c",
                    # stderr logging is nondeterministic (includes timing information)
                    "python3 inference.py 2>/dev/null",
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

if __name__ == "__main__":
    print(_sdxl("{prompt: hello, seed: 99}"))
    print(_sdxl("{prompt: 'hello world', seed: 99}"))