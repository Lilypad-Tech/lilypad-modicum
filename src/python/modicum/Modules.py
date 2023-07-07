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

modules = {
    "stable_diffusion": _stable_diffusion,
    "cowsay": _cowsay,
    "filecoin_data_prep": _filecoin_data_prep,
    "deterministic_wasm": _deterministic_wasm,
}