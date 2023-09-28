"""
DIY: module - runAny
runAny: module enables you to run and test any module prior to PR approval
"""

import dataclasses
import json
from dataclasses import dataclass
from typing import List

import yaml


@dataclass
class App:
    image: str
    params: str
    entrypoint: List[str]
    envVars: List[str] = None
    concurrency: int = 1
    engine: str = "Docker"

    jobContext: dict = None

    network: str = "None"

    publisherSpec: dict = None
    resources: dict = None  # {"GPU": "1"}

    timeout: int = 1800

    verifier: str = "Noop"

    wasm: dict = None

    outputs: List[dict] = None

    def __post_init__(self):
        self.envVars = self.envVars or []
        self.jobContext = self.jobContext or {}
        self.publisherSpec = self.publisherSpec or {"Type": "Estuary"}
        self.outputs = self.outputs or [
            {
                "Name": "outputs",
                "StorageSource": "IPFS",
                "path": "/outputs"
            }
        ]
        self.wasm = self.wasm or {"EntryModule": {}}
        self.resources = self.resources or {}

    @property
    def json(self) -> str:
        self_dict = dataclasses.asdict(self)
        json_str = json.dumps(self_dict)
        return json_str

    @staticmethod
    def loads(json_str: str) -> 'App':
        args = json.loads(json_str)
        return App(**args)


def _run_any(params: str):
    app: App = None

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
                "Concurrency": app.concurrency
            },
            "Docker": {
                "Entrypoint": app.entrypoint,
                "Image": app.image,
                "EnvironmentVariables": app.envVars
            },
            "Engine": app.engine,
            "Language": {
                "JobContext": app.jobContext
            },
            "Network": {
                "Type": app.network,
            },
            "PublisherSpec": app.publisherSpec,
            "Resources": app.resources,
            "Timeout": app.timeout,
            "Verifier": app.verifier,
            "Wasm": app.wasm,
            "outputs": app.outputs,
        }
    }


if __name__ == "__main__":
    a = App()
    print(a.json)
    print(_run_any(a.json))
    print(_run_any(App(seed=1).json))

    input_str = '{"train_cmd": "train_v2", "t": "linear-regression.ipynb", "i": "/app/samples/sample_v3/sample_v3.zip", "seed": 2}'
    a = App.loads(input_str)
    assert a.seed == 2
    print(_run_any(input_str))