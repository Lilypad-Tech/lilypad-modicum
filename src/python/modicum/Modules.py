from web3 import Web3
# TODO write a guide here for how people should make modules FULLY DETERMINISTIC
# TODO: include docker image hashes below

from modules.cowsay import _cowsay
from modules.deterministic_wasm import _deterministic_wasm
from modules.filecoin_data_prep import _filecoin_data_prep
from modules.stable_diffusion import _stable_diffusion

def get_bacalhau_jobspec(template_name, params):
    """
    Given a template and arbitary parameters for it, return a bacalhau jobspec
    as python dict.

    Caller of this method is responsible for writing it to a yaml file and then
    calling `bacalhau create <file.yaml>` on the ResourceProvider
    """
    return modules[template_name](params)

def get_bacalhau_jobprice(template_name):
    return Web3.to_wei(modules[template_name].price, 'ether')

modules = {
    "stable_diffusion:v0.0.1": _stable_diffusion,
    "cowsay:v0.0.1": _cowsay,
    "filecoin_data_prep:v0.0.1": _filecoin_data_prep,
    "deterministic_wasm:v0.0.1": _deterministic_wasm,
}