import yaml

def _filecoin_data_prep(params: str):
    """
    params["s3_bucket", "s3_key", "s3_region"]
    e.g.
        "s3_bucket": "noaa-goes16",
        "s3_key": "ABI-L1b-RadC/2000/001/12/OR_ABI-L1b-RadC-M3C01*",
        "s3_region": "us-east-1" (optional)

    or, use ipfs input:
        "ipfs_cid": "bafybeiah7ib5mhzlckolwlkwquzf772wl6jdbhtbuvnbuo5arq7pcs4ubm"

    # TODO: add s3_endpoint! (to support S3-compatible endpoints other than real S3)
    # TODO: https://github.com/bacalhau-project/MODICUM/issues/9
    """
    if params.startswith("{"):
        params = yaml.safe_load(params)
    else:
        raise Exception("Please set params to yaml like {seed: 42, 'images_cid': 'Qm...'} where images_cid contains an images.zip with training images in")

    inputs = []
    if "ipfs_cid" in params:
        inputs.append(
                {"CID": params["ipfs_cid"],
                 "Name": f"ipfs://{params['ipfs_cid']}",
                 "StorageSource": "IPFS",
                 "path": "/input",
                 })
    elif "s3_bucket" in params:
        inputs.append({
            "Name": "s3-input",
            "S3": {
                "Bucket": params["s3_bucket"],
                "Key": params["s3_key"],
                "Region": params.get("s3_region", "us-east-1")
            },
            "StorageSource": "S3",
            "path": "/input"
        })

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
                    "data-prep", "fil-data-prep",
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
            "inputs": inputs,
        }
    }
