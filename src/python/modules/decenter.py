"""
DIY: module - DECENTER, decentralized infra for AI/ML training
ONLINE_PlAYGROUND: https://decenter-ai.streamlit.app

"""

import dataclasses
import json
from dataclasses import dataclass

import yaml

CPU_CONFIG = {
    500: "500m",
    2: "2",
    8: "8",
}



@dataclass
class App:
    train_cmd: str = "train_v2"
    t: str = "linear-regression.ipynb"
    i: str = "/app/samples/sample_v3/sample_v3.zip"
    seed: int = 0  # not used but for deterministic
    image_tag: str = "v1.5.5" #stable version checkout stable releases over https://github.com/DeCenter-AI/compute.decenter-ai/releases
    
    gpu: int =1 #1-8
    cpu: int|str = CPU_CONFIG[8]
    memory: str = "1Gb"
    
    def __post_init__(self):
        pass
        

    @property
    def json(self) -> str:
        self_dict = dataclasses.asdict(self)
        json_str = json.dumps(self_dict)
        return json_str

    @staticmethod
    def loads(json_str: str) -> 'App':
        args = json.loads(json_str)
        return App(**args)


def _decenter(params: str):
    app = App()

    if params.startswith("{"):
        params = yaml.safe_load(params)
        # app = App.loads(params)
        app = App(**params)
    # else:
    #     raise Exception(f"Please set params to a dict like {app.json}")
    # FIXME add it in future

    if not isinstance(app, App):
        raise Exception(f"Please set params to a dict like {app.json}")

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
                    "/app/venv/bin/python",
                    "main.py",
                    app.train_cmd,
                    f"-t={app.t}",
                    f"-i={app.i}",
                    "2>/dev/null",
                    # "> /dev/null 2>&1"
                ],
                "Image": f"ghcr.io/decenter-ai/compute:{app.image_tag}",
                "EnvironmentVariables": [
                    # f"PROMPT={params.get('prompt', 'question mark floating in space')}",
                    # f"RANDOM_SEED={params.get('seed', 0)}",
                    "OUTPUT_DIR=/outputs/",
                    "DATA_DIR=/data",
                    #  FIXME: use appropriate values , this is the default val

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
                "GPU": str(app.gpu),
                "CPU": str(app.cpu),
                "MEMORY": str(app.memory),
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
    a = App()
    print(a.json)
    print(_decenter(a.json))
    print(_decenter(App(seed=1).json))

    input_str = '{"train_cmd": "train_v2", "t": "linear-regression.ipynb", "i": "/app/samples/sample_v3/sample_v3.zip", "seed": 2}'
    a = App.loads(input_str)
    assert a.seed == 2
    print(_decenter(input_str))
