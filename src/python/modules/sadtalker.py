import yaml

def _sadtalker(params: str):
    if params.startswith("{"):
        params = yaml.safe_load(params)
    else:
        raise Exception("Please set params to a dict like {'driven_audio': 'path/to/audio', 'source_image': 'path/to/image'}")
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
                    "python",
                    "inference.py",
                    "--driven_audio",
                    params.get('driven_audio', '/inputs/input.wav'),
                    "--source_image",
                    params.get('source_image', '/inputs/source.png'),
                    "--expression_scale"
                    "1.0",
                    "--still",
                    "--result_dir",
                    "/outputs"
                ],
                "Image": "wawa9000/sadtalker:latest"
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