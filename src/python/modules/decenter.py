"""
DIY: module - DECENTER, decentralized infra for AI/ML training
ONLINE_PlAYGROUND: https://decenter-ai.streamlit.app

"""

import dataclasses
import json
from dataclasses import dataclass

import yaml


@dataclass
class App:
    train_cmd: str = "train_v2"
    t: str = "linear-regression.ipynb"
    i: str = "/app/samples/sample_v3/sample_v3.zip"
    seed: int = 0  # not used but for deterministic
    image_tag: str = "v1.5.0"

    @property
    def json(self) -> str:
        self_dict = dataclasses.asdict(self)
        json_str = json.dumps(self_dict)
        return json_str

    @staticmethod
    def loads(json_str: str) -> 'App':
        args = json.loads(json_str)
        return App(**args)
    # def to_dict(self):
    #     return {"train_cmd": self.train_cmd, "t": self.t, }


def _decenter(params: str):
    app = App()

    if params.startswith("{"):
        params = yaml.safe_load(params)
        # app = App.loads(params)
        # FIXME: no need of yaml safe load, but going with the sample provided
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
                    # "bash", "-c",
                    # stderr logging is nondeterministic (includes timing information)
                    # "python3 inference.py 2>/dev/null",
                    f"/app/venv/bin/python main.py {app.train_cmd}",
                    f"-t={app.t} -i={app.i}",
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
    a = App()
    print(a.json)
    print(_decenter(a.json))
    print(_decenter(App(seed=1).json))

    input_str = '{"train_cmd": "train_v2", "t": "linear-regression.ipynb", "i": "/app/samples/sample_v3/sample_v3.zip", "seed": 2}'
    a = App.loads(input_str)
    assert a.seed == 2
    print(_decenter(input_str))
