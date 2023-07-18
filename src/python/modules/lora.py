import yaml
import textwrap

IMAGE = "quay.io/lukemarsden/lora:v0.0.3"
MODEL_NAME = "runwayml/stable-diffusion-v1-5"

# Don't want to make this variable since the job is fixed price
NUM_IMAGES = 10

def _lora_training(params: str):
    if params.startswith("{"):
        params = yaml.safe_load(params)
    else:
        raise Exception("Please set params to yaml like {seed: 42, 'images_cid': 'Qm...'}")

    seed = params["seed"]
    images_cid = params["images_cid"]

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
                    'lora_pti',
                    f'--pretrained_model_name_or_path={MODEL_NAME}',
                    '--instance_data_dir=/input', '--output_dir=/output',
                    '--train_text_encoder', '--resolution=512',
                    '--train_batch_size=1',
                    '--gradient_accumulation_steps=4', '--scale_lr',
                    '--learning_rate_unet=1e-4',
                    '--learning_rate_text=1e-5', '--learning_rate_ti=5e-4',
                    '--color_jitter', '--lr_scheduler="linear"',
                    '--lr_warmup_steps=0',
                    '--placeholder_tokens="<s1>|<s2>"',
                    '--use_template="style"', '--save_steps=100',
                    '--max_train_steps_ti=1000',
                    '--max_train_steps_tuning=1000',
                    '--perform_inversion=True', '--clip_ti_decay',
                    '--weight_decay_ti=0.000', '--weight_decay_lora=0.001',
                    '--continue_inversion', '--continue_inversion_lr=1e-4',
                    '--device="cuda:0"', '--lora_rank=1'
                ],
                "Image": IMAGE,
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
            "inputs": {
                {
                    "CID": images_cid,
                    "Name": "lora_input",
                    "StorageSource": "IPFS",
                    "path": "/input",

                },
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

def _lora_inference(params: str):
    if params.startswith("{"):
        params = yaml.safe_load(params)
    else:
        raise Exception("Please set params to yaml like {seed: 42, 'lora_cid': 'Qm...', "+
                        "prompt: 'an astronaut in the style of <s1><s2>'} "+
                        "where lora_cid is the output cid of the above step")

    # TODO add a default we pin
    lora_cid = params["lora_cid"]
    seed = params.get("seed", 42)
    prompt = params.get("prompt", "question mark floating in space")
    finetune_weighting = params.get("finetune_weighting", 0.5)

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
                "EnvironmentVariables": [
                    f"PROMPT={prompt}",
                    f"RANDOM_SEED={seed}",
                    f"FINETUNE_WEIGHTING={finetune_weighting}",
                    "HF_HUB_OFFLINE=1",
                ],
                "Entrypoint": [
                    'python3',
                    '-c',
                    # dedent
                    textwrap.dedent(f"""
                        from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
                        import torch
                        from lora_diffusion import tune_lora_scale, patch_pipe

                        model_id = "{MODEL_NAME}"

                        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16).to(
                            "cuda"
                        )
                        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

                        prompt = os.getenv("PROMPT")
                        seed = int(os.getenv("RANDOM_SEED"))
                        torch.manual_seed(seed)

                        patch_pipe(
                            pipe,
                            "/input/final_lora.safetensors",
                            patch_text=True,
                            patch_ti=True,
                            patch_unet=True,
                        )

                        coeff = float(os.getenv("FINETUNE_WEIGHTING"), 0.5)
                        tune_lora_scale(pipe.unet, coeff)
                        tune_lora_scale(pipe.text_encoder, coeff)

                        image = pipe(prompt, num_inference_steps=50, guidance_scale=7).images[0]
                        image.save(f"/output/image-{{seed}}.jpg")
                        image
                        """)
                ],
                "Image": IMAGE,
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
            "inputs": {
                {
                    "CID": lora_cid,
                    "Name": "lora_input",
                    "StorageSource": "IPFS",
                    "path": "/input",

                },
            },
            "outputs": [
                {
                    "Name": "output",
                    "StorageSource": "IPFS",
                    "path": "/output"
                },
            ]
        }
    }