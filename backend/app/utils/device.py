import torch


def get_device(pref: str = "auto") -> torch.device:
    """Pick CPU / CUDA / Apple-MPS automatically (or honour an explicit choice)."""
    if pref != "auto":
        return torch.device(pref)
    if torch.cuda.is_available():
        return torch.device("cuda")
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
