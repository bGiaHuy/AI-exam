#!/usr/bin/env python3
"""
scripts/verify_training_lineage_handoff.py
-----------------------------------------
Sprint 3.2A Verification Script for Training-Lineage Handoff (Pass 1.3).
Performs strict, read-only integrity verification:
  1. Checks canonical directory contains exactly the 10 authorized files.
  2. Verifies SHA-256 of artifact_hashes.csv matches Pass 1.3 expected hash.
  3. Verifies file size and SHA-256 of all 9 payload files against artifact_hashes.csv.
  4. Validates lineage_manifest.json schema, Pass 1.3 version, and mandatory technical assertions:
     - D-01 == CLOSED
     - D-02 == OPEN
     - training_resume_detected == True
     - resume_boundary_observed_before_epoch == 6
     - initial_pretrained_checkpoint_status == UNRESOLVED
     - best_checkpoint_source_epoch_status == BEST_CHECKPOINT_SOURCE_EPOCH_UNRESOLVED
     - multiv_and_test_data_role.role == external_challenge_previously_seen
  5. Verifies training_data_phone.redacted.yaml contains EVIDENCE_ONLY header without resolving path.
  6. Confirms absence of unredacted personal user directory paths.

Exit code 0 on SUCCESS, non-zero on FAILURE.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

# Pass 1.3 Expected SHA-256 for artifact_hashes.csv
EXPECTED_ARTIFACT_HASHES_SHA256 = "61c78a5340955c41357146361684da698610270ff3cafaa36db8cf93e08243e1"

# Canonical list of exactly 10 authorized files
CANONICAL_FILES = {
    "README_mobilephone_v3.txt",
    "README_mobilephone2_v1.txt",
    "README_mobilephone3_v1.txt",
    "results.csv",
    "SPRINT_2_2A_CORRECTED_REPORT.md",
    "training_data_phone.redacted.yaml",
    "args.yaml",
    "HANDOFF_README.md",
    "lineage_manifest.json",
    "artifact_hashes.csv"
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_handoff(target_dir: Path) -> bool:
    print(f"=== SPRINT 3.2A TRAINING LINEAGE HANDOFF VERIFICATION ===")
    print(f"Target directory: {target_dir.resolve()}")
    
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"[FAIL] Target directory does not exist: {target_dir}")
        return False

    # 1. Check directory contents: must have all 10 canonical files, no unauthorized extras
    actual_files = {p.name for p in target_dir.iterdir() if p.is_file()}
    missing_files = CANONICAL_FILES - actual_files
    extra_files = actual_files - CANONICAL_FILES

    if missing_files:
        print(f"[FAIL] Missing canonical files: {missing_files}")
        return False
    if extra_files:
        print(f"[FAIL] Unauthorized extra files found in canonical lineage dir: {extra_files}")
        return False
    print(f"[OK] Directory contains exactly the 10 canonical files.")

    # 2. Check SHA-256 of artifact_hashes.csv itself
    hash_manifest_path = target_dir / "artifact_hashes.csv"
    actual_manifest_hash = sha256_file(hash_manifest_path)
    if actual_manifest_hash != EXPECTED_ARTIFACT_HASHES_SHA256:
        print(f"[FAIL] artifact_hashes.csv SHA256 mismatch:")
        print(f"       Expected: {EXPECTED_ARTIFACT_HASHES_SHA256}")
        print(f"       Actual:   {actual_manifest_hash}")
        return False
    print(f"[OK] artifact_hashes.csv integrity verified ({actual_manifest_hash[:16]}...).")

    # 3. Read artifact_hashes.csv and verify the 9 payload files
    payload_records = {}
    with open(hash_manifest_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            payload_records[row["filename"]] = {
                "size_bytes": int(row["size_bytes"]),
                "sha256": row["sha256"].strip()
            }

    if len(payload_records) != 9:
        print(f"[FAIL] artifact_hashes.csv must contain exactly 9 records, found {len(payload_records)}")
        return False

    for fname, meta in payload_records.items():
        fpath = target_dir / fname
        if not fpath.exists():
            print(f"[FAIL] Referenced file {fname} does not exist.")
            return False
        
        actual_size = fpath.stat().st_size
        if actual_size != meta["size_bytes"]:
            print(f"[FAIL] Size mismatch for {fname}: expected {meta['size_bytes']}, got {actual_size}")
            return False
        
        actual_sha = sha256_file(fpath)
        if actual_sha != meta["sha256"]:
            print(f"[FAIL] SHA256 mismatch for {fname}:")
            print(f"       Expected: {meta['sha256']}")
            print(f"       Actual:   {actual_sha}")
            return False
        print(f"[OK] Verified payload: {fname} ({actual_size} bytes, hash: {actual_sha[:16]}...)")

    # 4. Parse lineage_manifest.json and check mandatory assertions
    manifest_path = target_dir / "lineage_manifest.json"
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[FAIL] Could not parse lineage_manifest.json: {e}")
        return False

    # Check report version is Pass 1.3
    report_ver = manifest.get("report_version", "")
    if "Pass 1.3" not in report_ver:
        print(f"[FAIL] Manifest report_version is not Pass 1.3: {report_ver}")
        return False
    print(f"[OK] Manifest report_version confirmed: '{report_ver}'")

    # Check D-01 and D-02 blocker states
    blockers = manifest.get("blocker_status", {})
    if blockers.get("D-01_training_dataset_lineage") != "CLOSED":
        print(f"[FAIL] D-01 must be CLOSED in Pass 1.3 manifest, got: {blockers.get('D-01_training_dataset_lineage')}")
        return False
    if blockers.get("D-02_independent_untouched_holdout_evaluation") != "OPEN":
        print(f"[FAIL] D-02 must be OPEN in manifest, got: {blockers.get('D-02_independent_untouched_holdout_evaluation')}")
        return False
    print(f"[OK] Blocker statuses in manifest: D-01=CLOSED, D-02=OPEN")

    # Check checkpoint info
    ckpt = manifest.get("checkpoint_info", {})
    if ckpt.get("training_resume_detected") is not True:
        print(f"[FAIL] checkpoint_info.training_resume_detected must be True")
        return False
    if ckpt.get("resume_boundary_observed_before_epoch") != 6:
        print(f"[FAIL] checkpoint_info.resume_boundary_observed_before_epoch must be 6, got: {ckpt.get('resume_boundary_observed_before_epoch')}")
        return False
    if ckpt.get("initial_pretrained_checkpoint_status") != "UNRESOLVED":
        print(f"[FAIL] checkpoint_info.initial_pretrained_checkpoint_status must be UNRESOLVED, got: {ckpt.get('initial_pretrained_checkpoint_status')}")
        return False
    print(f"[OK] Checkpoint resume evidence confirmed (resumed before epoch 6, initial pretrained UNRESOLVED).")

    # Check best epoch status
    metrics = manifest.get("training_metrics_extrema", {})
    if metrics.get("best_checkpoint_source_epoch_status") != "BEST_CHECKPOINT_SOURCE_EPOCH_UNRESOLVED":
        print(f"[FAIL] best_checkpoint_source_epoch_status must be BEST_CHECKPOINT_SOURCE_EPOCH_UNRESOLVED")
        return False
    print(f"[OK] Best checkpoint source epoch status: BEST_CHECKPOINT_SOURCE_EPOCH_UNRESOLVED.")

    # Check MultiV role
    multiv = manifest.get("multiv_and_test_data_role", {})
    if multiv.get("role") != "external_challenge_previously_seen":
        print(f"[FAIL] multiv role must be external_challenge_previously_seen, got: {multiv.get('role')}")
        return False
    print(f"[OK] MultiV role confirmed: external_challenge_previously_seen.")

    # 5. Verify training_data_phone.redacted.yaml has evidence-only header
    yaml_path = target_dir / "training_data_phone.redacted.yaml"
    yaml_content = yaml_path.read_text(encoding="utf-8")
    if "EVIDENCE_ONLY — NOT AN EXECUTABLE DATASET CONFIG" not in yaml_content:
        print(f"[FAIL] training_data_phone.redacted.yaml missing EVIDENCE_ONLY header banner.")
        return False
    print(f"[OK] Redacted YAML verified as evidence-only (not treated as executable config).")

    # 6. Check for unredacted personal user directory paths across all text files
    for fname in CANONICAL_FILES:
        fpath = target_dir / fname
        try:
            txt = fpath.read_text(encoding="utf-8", errors="ignore").lower()
            if "c:\\users\\" in txt or "c:/users/" in txt or "/home/" in txt:
                print(f"[FAIL] Unredacted personal path detected in {fname}")
                return False
        except Exception:
            pass
    print(f"[OK] No unredacted personal filesystem paths found.")

    print(f"=== SPRINT 3.2A VERIFICATION RESULT: PASS (All criteria satisfied) ===")
    return True

def main():
    parser = argparse.ArgumentParser(description="Verify Sprint 2.2A Pass 1.3 Training Lineage Handoff")
    parser.add_argument(
        "--dir",
        default="reports/evidence/training_lineage",
        help="Path to canonical training lineage directory (default: reports/evidence/training_lineage)"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    target_dir = (repo_root / args.dir).resolve() if not Path(args.dir).is_absolute() else Path(args.dir)

    success = verify_handoff(target_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
