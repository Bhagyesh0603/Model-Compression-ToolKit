"""zoo/ path resolution: DEFAULT_ROOT must land on the repo's real data/ dir.

`git mv compresskit/data.py compresskit/zoo/data.py` (and the har.py
equivalent) moved these files one directory deeper without updating their
`.parent.parent`-based relative path to the repo root, so DEFAULT_ROOT
silently resolved to a nonexistent `compresskit/data` instead of the real,
already-downloaded `data/` at the repo root.
"""

from pathlib import Path

from compresskit.zoo import data, har

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_cifar_default_root_resolves_to_the_repo_root_data_dir():
    assert data.DEFAULT_ROOT == REPO_ROOT / "data"


def test_har_default_root_resolves_to_the_repo_root_data_dir():
    assert har.DEFAULT_ROOT == REPO_ROOT / "data" / "har" / "Human Action Recognition"


# --- bring-your-own-model checkpoints -----------------------------------------
import pytest
import torch
import torch.nn as nn

from compresskit.zoo.train import load_model, save_model


def _tiny():
    return nn.Sequential(nn.Conv2d(3, 4, 3), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(4, 10))


def test_load_model_reads_compresskit_checkpoints(tmp_path):
    save_model(_tiny(), tmp_path / "ck.pt", {"arch": "tiny", "accuracy": 0.5})
    model, meta = load_model(tmp_path / "ck.pt")
    assert isinstance(model, nn.Module) and meta["arch"] == "tiny"


def test_load_model_accepts_a_plain_torch_save_of_a_whole_model(tmp_path):
    torch.save(_tiny(), tmp_path / "plain.pt")
    model, meta = load_model(tmp_path / "plain.pt")
    assert isinstance(model, nn.Module) and not model.training
    assert meta == {}


def test_load_model_explains_that_a_state_dict_alone_is_not_enough(tmp_path):
    torch.save(_tiny().state_dict(), tmp_path / "weights.pt")
    with pytest.raises(ValueError, match="state_dict"):
        load_model(tmp_path / "weights.pt")
