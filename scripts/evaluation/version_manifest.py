"""
================================================================================
VERSION MANIFEST & DATASET FINGERPRINT GENERATOR (SPRINT 2.1A)
================================================================================
Captures environment, hardware, weights hash, deterministic dataset fingerprint,
git state, and execution parameters to produce a best-effort reproducibility manifest.
================================================================================
"""

import os
import sys
import glob
import hashlib
import platform
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

import torch
import numpy as np
import cv2

try:
    import ultralytics
    ULTRALYTICS_VERSION = ultralytics.__version__
except ImportError:
    ULTRALYTICS_VERSION = "unknown"


def get_file_sha256(file_path: str) -> Optional[str]:
    if not file_path or not os.path.exists(file_path):
        return None
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_dataset_fingerprint(dataset_dir: str, split: Optional[str] = None) -> str:
    """
    Computes a deterministic SHA-256 fingerprint over all data files in the specified dataset
    and split. The fingerprint changes if any image, label, metadata, or config file changes,
    or if files are added/deleted.
    """
    if not os.path.exists(dataset_dir):
        return "empty_or_nonexistent_dataset"

    files_to_hash: List[str] = []

    # 1. Config / YAML files in dataset root
    for f in os.listdir(dataset_dir):
        if f.endswith((".yaml", ".yml")):
            files_to_hash.append(os.path.join(dataset_dir, f))

    # 2. Metadata files
    meta_dir = os.path.join(dataset_dir, "metadata")
    if os.path.exists(meta_dir):
        for root, _, fnames in os.walk(meta_dir):
            for fn in fnames:
                if fn.endswith((".csv", ".json", ".txt")):
                    files_to_hash.append(os.path.join(root, fn))

    # 3. Annotations files (e.g. posture)
    ann_dir = os.path.join(dataset_dir, "annotations")
    if os.path.exists(ann_dir):
        for root, _, fnames in os.walk(ann_dir):
            for fn in fnames:
                if fn.endswith((".csv", ".json", ".txt")):
                    files_to_hash.append(os.path.join(root, fn))

    # 4. Images / Videos and Labels
    subdirs_to_check = ["images", "labels", "videos"]
    for sdir in subdirs_to_check:
        base_sdir = os.path.join(dataset_dir, sdir)
        if not os.path.exists(base_sdir):
            continue
        if split:
            sp_dir = os.path.join(base_sdir, split)
            if os.path.exists(sp_dir):
                for root, _, fnames in os.walk(sp_dir):
                    for fn in fnames:
                        files_to_hash.append(os.path.join(root, fn))
        else:
            for root, _, fnames in os.walk(base_sdir):
                for fn in fnames:
                    files_to_hash.append(os.path.join(root, fn))

    if not files_to_hash:
        return "empty_dataset"

    # Compute individual file hashes and normalize paths relative to dataset_dir
    file_records: List[Tuple[str, str]] = []
    for fp in files_to_hash:
        rel_p = os.path.relpath(fp, dataset_dir).replace("\\", "/")
        f_hash = get_file_sha256(fp) or "missing"
        file_records.append((rel_p, f_hash))

    # Sort deterministically by relative path
    file_records.sort(key=lambda x: x[0])

    # Compute master hash over concatenated entries
    master_hasher = hashlib.sha256()
    for rel_p, f_hash in file_records:
        entry = f"{rel_p}:{f_hash}\n"
        master_hasher.update(entry.encode("utf-8"))

    return master_hasher.hexdigest()


def get_git_info() -> Dict[str, Any]:
    info = {
        "commit": None,
        "branch": None,
        "dirty": False,
        "diff_stat": None,
        "modified_or_untracked": []
    }
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        info["commit"] = commit
    except Exception:
        info["commit"] = "unknown"

    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        info["branch"] = branch
    except Exception:
        info["branch"] = "unknown"

    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL).decode().strip()
        if status:
            info["dirty"] = True
            info["modified_or_untracked"] = [line.strip() for line in status.splitlines()]
            diff_stat = subprocess.check_output(["git", "diff", "--stat"], stderr=subprocess.DEVNULL).decode().strip()
            info["diff_stat"] = diff_stat
    except Exception:
        pass

    return info


def get_hardware_info() -> Dict[str, Any]:
    gpu_name = "CPU"
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        gpu_name = f"{torch.cuda.get_device_name(0)} (CUDA active)"

    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "cuda_available": gpu_available,
        "device_name": gpu_name,
    }


def create_version_manifest(
    weights_path: Optional[str] = None,
    dataset_dir: Optional[str] = None,
    dataset_metadata_path: Optional[str] = None,
    split: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    seed: int = 0
) -> Dict[str, Any]:
    weights_hash = get_file_sha256(weights_path) if weights_path else None
    dataset_hash = get_file_sha256(dataset_metadata_path) if dataset_metadata_path else None
    dataset_fp = compute_dataset_fingerprint(dataset_dir, split) if dataset_dir else None

    return {
        "manifest_type": "reproducibility_manifest",
        "evaluator_version": "2.1A",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(sys.argv),
        "seed": seed,
        "git": get_git_info(),
        "weights": {
            "path": weights_path,
            "sha256": weights_hash
        },
        "dataset": {
            "dataset_dir": dataset_dir,
            "split": split,
            "metadata_path": dataset_metadata_path,
            "metadata_sha256": dataset_hash,
            "dataset_fingerprint": dataset_fp
        },
        "config": config or {},
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "ultralytics": ULTRALYTICS_VERSION,
            "numpy": np.__version__,
            "opencv": cv2.__version__
        },
        "hardware": get_hardware_info()
    }


if __name__ == "__main__":
    import json
    manifest = create_version_manifest()
    print(json.dumps(manifest, indent=2))
