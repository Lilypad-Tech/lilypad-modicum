import json

def _fastchat(params: str):
    
    if params.startswith("{"):
        params = json.loads(params)
    else:
        question = params
        params = {"template": "You are chatbot. \n question: {question} \n anwser:", "parameters": {"question": question}}
    print(params)
    cmd = "python3 main.py --t " + params['template'] + "--p " + params['parameters'] + " 2>/dev/null"
    print(cmd)
    if not isinstance(params, dict):
        raise Exception('Please set params to a dict like {"template": "You are chatbot. \n question: {question} \n anwser:", "parameters": {"question":"What is an AI bot"}}')
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
                    cmd,
                ],
                "Image": "xqua/carpai-demo-repo:v0.2",
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
                    "Name": "output",
                    "StorageSource": "IPFS",
                    "path": "/output"
                }
            ]
        }
    }

if __name__ == "__main__":
    print(_fastchat('{"template": "You are chatbot. \n question: {question} \n anwser:", "parameters": {"question":question}}'))
