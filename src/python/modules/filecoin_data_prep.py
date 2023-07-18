def _filecoin_data_prep(params: dict):
    """
    params["s3_bucket", "s3_key", "s3_region"]
    e.g.
        "s3_bucket": "noaa-goes16",
        "s3_key": "ABI-L1b-RadC/2000/001/12/OR_ABI-L1b-RadC-M3C01*",
        "s3_region": "us-east-1" (optional)

    # TODO: add s3_endpoint! (to support S3-compatible endpoints other than real S3)
    # TODO: https://github.com/bacalhau-project/MODICUM/issues/9
    """
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
                    "/usr/local/bin/data-prep", "fil-data-prep",
                      "--size", "100000000000", "--metadata", "meta.csv",
                      "--output", "/output/test", "/input",
                ],
                "Image": "quay.io/lilypad/go-fil-dataprep:v0.0.1",
                "EnvironmentVariables": [
                    # go-fil-dataprep is known not to be deterministic,
                    # hopefully doing this makes it be deterministic.
                    # XXX TO BE CONFIRMED
                    "GOMAXPROCS=1"
                ]
            },
            "Engine": "Docker",
            "Network": {
                "Type": "None"
            },
            "PublisherSpec": {
                "Type": "Estuary"
            },
            "Resources": {
                "GPU": ""
            },
            "Timeout": 1800,
            "Verifier": "Noop",
            "output": [
                {
                    "Name": "output",
                    "StorageSource": "IPFS",
                    "path": "/output"
                }
            ],
            "inputs": [
                {
                    "Name": "s3-input",
                    "S3": {
                        "Bucket": params["s3_bucket"],
                        "Key": params["s3_key"],
                        "Region": params.get("s3_region", "us-east-1")
                    },
                    "StorageSource": "S3",
                    "path": "/input"
                }
            ]
        }
    }

_filecoin_data_prep.requireGPU = False