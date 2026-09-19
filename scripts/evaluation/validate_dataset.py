"""
================================================================================
DATASET PROTOCOL, INTEGRITY & LEAKAGE VALIDATOR (SPRINT 2.1A)
================================================================================
Strict validation protocol for Phone Detection and Head-Turning datasets:
- Enforces strict zero-leakage by source_video_id, session_id, and content hash.
- Validates image-label correspondence and distractor / empty label policy.
- Checks strict YOLO bounding box coordinates (finite, strictly inside [0, 1]).
- Detects duplicate sample_id/path, orphan images/labels, corrupt images,
  split mismatches, and events exceeding video duration.
================================================================================
"""

import os
import sys
import csv
import math
import hashlib
import argparse
from typing import Dict, List, Set, Any, Tuple, Optional

import cv2


REQUIRED_SAMPLE_COLUMNS = [
    "sample_id", "relative_path", "source_video_id", "session_id",
    "subject_id_anonymous", "scene_id", "camera_id", "timestamp_seconds",
    "split", "has_phone", "has_distractor", "distractor_types", "lighting", "occlusion",
    "distance_group", "source_provenance", "usage_permission"
]

REQUIRED_EVENT_COLUMNS = [
    "event_id", "video_id", "target_id_anonymous", "behavior",
    "start_seconds", "end_seconds", "direction", "annotator", "review_status", "split"
]

VALID_SPLITS = {"train", "val", "test"}
VALID_BEHAVIORS = {"NORMAL", "HEAD_TURNING"}
VALID_REVIEW_STATUSES = {"APPROVED", "PENDING", "REJECTED"}


def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class DatasetValidator:
    def __init__(self, phone_dir: Optional[str] = None, posture_dir: Optional[str] = None):
        self.phone_dir = phone_dir
        self.posture_dir = posture_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}

    def log_error(self, msg: str):
        self.errors.append(msg)

    def log_warning(self, msg: str):
        self.warnings.append(msg)

    def validate_phone_dataset(self) -> Dict[str, Any]:
        phone_stats: Dict[str, Any] = {
            "samples_count": 0,
            "splits": {},
            "hard_negatives": 0,
            "distractors": 0,
            "phones_positive": 0,
            "leakage_checks": {
                "source_video_leakage": False,
                "session_leakage": False,
                "content_hash_leakage": False
            }
        }
        if not self.phone_dir or not os.path.exists(self.phone_dir):
            self.log_warning(f"Phone dataset directory not found: {self.phone_dir}")
            return phone_stats

        samples_csv = os.path.join(self.phone_dir, "metadata", "samples.csv")
        if not os.path.exists(samples_csv):
            self.log_error(f"Missing samples metadata: {samples_csv}")
            return phone_stats

        # 1. Validate samples.csv header and content
        with open(samples_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            missing_cols = [c for c in REQUIRED_SAMPLE_COLUMNS if c not in header]
            if missing_cols:
                self.log_error(f"samples.csv missing required columns: {missing_cols}")
                return phone_stats

            seen_sample_ids: Set[str] = set()
            seen_rel_paths: Set[str] = set()
            referenced_labels: Set[str] = set()
            referenced_images: Set[str] = set()

            video_to_splits: Dict[str, Set[str]] = {}
            session_to_splits: Dict[str, Set[str]] = {}
            subject_to_splits: Dict[str, Set[str]] = {}
            hash_to_split: Dict[str, Tuple[str, str]] = {}  # hash -> (split, rel_path)

            count = 0
            for idx, row in enumerate(reader, start=2):
                count += 1
                sample_id = row.get("sample_id", "").strip()
                rel_path = row.get("relative_path", "").strip()
                vid_id = row.get("source_video_id", "").strip()
                sess_id = row.get("session_id", "").strip()
                subj_id = row.get("subject_id_anonymous", "").strip()
                split = row.get("split", "").strip().lower()
                has_phone_raw = row.get("has_phone", "").strip().lower()
                has_distractor_raw = row.get("has_distractor", "").strip().lower()

                # Duplicate checks
                if not sample_id:
                    self.log_error(f"Row {idx}: sample_id is empty.")
                elif sample_id in seen_sample_ids:
                    self.log_error(f"Row {idx}: Duplicate sample_id '{sample_id}'.")
                else:
                    seen_sample_ids.add(sample_id)

                if not rel_path:
                    self.log_error(f"Row {idx}: relative_path is empty.")
                elif rel_path in seen_rel_paths:
                    self.log_error(f"Row {idx}: Duplicate relative_path '{rel_path}'.")
                else:
                    seen_rel_paths.add(rel_path)

                # Enum validation
                if split not in VALID_SPLITS:
                    self.log_error(f"Row {idx}: Invalid split '{split}'. Must be one of {VALID_SPLITS}")
                    continue

                if has_phone_raw not in ("true", "false", "1", "0", "yes", "no"):
                    self.log_error(f"Row {idx}: Invalid enum for has_phone: '{has_phone_raw}'")
                if has_distractor_raw and has_distractor_raw not in ("true", "false", "1", "0", "yes", "no"):
                    self.log_error(f"Row {idx}: Invalid enum for has_distractor: '{has_distractor_raw}'")

                has_phone = has_phone_raw in ("true", "1", "yes")
                has_distractor = has_distractor_raw in ("true", "1", "yes")

                if has_phone:
                    phone_stats["phones_positive"] += 1
                if has_distractor:
                    phone_stats["distractors"] += 1
                if not has_phone and has_distractor:
                    phone_stats["hard_negatives"] += 1

                # Physical split mismatch check: relative_path should start with images/<split>/
                norm_rel_path = rel_path.replace("\\", "/")
                expected_prefix = f"images/{split}/"
                if not norm_rel_path.startswith(expected_prefix):
                    self.log_error(
                        f"Row {idx}: Split mismatch. Metadata split is '{split}', "
                        f"but relative_path '{rel_path}' does not start with '{expected_prefix}'"
                    )

                phone_stats["splits"][split] = phone_stats["splits"].get(split, 0) + 1

                # Leakage tracker
                if vid_id:
                    video_to_splits.setdefault(vid_id, set()).add(split)
                if sess_id:
                    session_to_splits.setdefault(sess_id, set()).add(split)
                if subj_id:
                    subject_to_splits.setdefault(subj_id, set()).add(split)

                # Physical image check
                img_full_path = os.path.join(self.phone_dir, rel_path)
                if not os.path.exists(img_full_path):
                    self.log_error(f"Row {idx}: Image file not found: '{rel_path}'")
                else:
                    referenced_images.add(os.path.abspath(img_full_path))
                    # Check if corrupt or unreadable image
                    if os.path.getsize(img_full_path) == 0:
                        self.log_error(f"Row {idx}: Corrupt image (0 bytes): '{rel_path}'")
                    else:
                        img_mat = cv2.imread(img_full_path)
                        if img_mat is None or img_mat.size == 0:
                            self.log_error(f"Row {idx}: Corrupt or unreadable image: '{rel_path}'")

                    # Check duplicate hash across splits
                    img_hash = compute_file_sha256(img_full_path)
                    if img_hash in hash_to_split:
                        prev_split, prev_path = hash_to_split[img_hash]
                        if prev_split != split:
                            self.log_error(
                                f"CONTENT HASH LEAKAGE: Image '{rel_path}' in split '{split}' "
                                f"has identical SHA-256 to '{prev_path}' in split '{prev_split}'!"
                            )
                            phone_stats["leakage_checks"]["content_hash_leakage"] = True
                    else:
                        hash_to_split[img_hash] = (split, rel_path)

                    # Corresponding label check
                    base_name = os.path.splitext(os.path.basename(rel_path))[0]
                    label_path = os.path.join(self.phone_dir, "labels", split, f"{base_name}.txt")
                    if not os.path.exists(label_path):
                        self.log_error(f"Image '{rel_path}' exists but missing label file: {label_path}")
                    else:
                        referenced_labels.add(os.path.abspath(label_path))
                        self._validate_yolo_label(label_path, has_phone, has_distractor, rel_path)

            phone_stats["samples_count"] = count

            # Check orphan label files on disk
            for sp in VALID_SPLITS:
                sp_labels_dir = os.path.join(self.phone_dir, "labels", sp)
                if os.path.exists(sp_labels_dir):
                    for fname in os.listdir(sp_labels_dir):
                        if fname.endswith(".txt"):
                            lbl_full = os.path.abspath(os.path.join(sp_labels_dir, fname))
                            if lbl_full not in referenced_labels:
                                self.log_error(f"Orphan label file without metadata/image: {lbl_full}")

            # Check video leakage
            for vid, sps in video_to_splits.items():
                if len(sps) > 1:
                    self.log_error(f"SOURCE VIDEO LEAKAGE: source_video_id '{vid}' appears in multiple splits: {sps}")
                    phone_stats["leakage_checks"]["source_video_leakage"] = True

            # Check session leakage
            for sid, sps in session_to_splits.items():
                if len(sps) > 1:
                    self.log_error(f"SESSION LEAKAGE: session_id '{sid}' appears in multiple splits: {sps}")
                    phone_stats["leakage_checks"]["session_leakage"] = True

            # Check subject dispersion (warning)
            for sub, sps in subject_to_splits.items():
                if "train" in sps and "test" in sps:
                    self.log_warning(f"Subject '{sub}' appears in both 'train' and 'test' splits.")

            if len(session_to_splits) < 2 and count > 0:
                self.log_warning(
                    f"Insufficient session groups ({len(session_to_splits)}) to establish reliable train/val/test split."
                )

        return phone_stats

    def _validate_yolo_label(self, label_path: str, has_phone: bool, has_distractor: bool, rel_path: str):
        with open(label_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not has_phone:
            # Policy: Negative image (with or without distractors) must have 0 annotations
            if len(lines) > 0:
                self.log_error(
                    f"Label policy violation: '{rel_path}' has has_phone=False but label file "
                    f"'{label_path}' contains {len(lines)} annotations. Negatives must have empty label files."
                )
        else:
            if len(lines) == 0:
                self.log_error(
                    f"Label policy violation: '{rel_path}' has has_phone=True but label file "
                    f"'{label_path}' is empty."
                )

        for l_idx, line in enumerate(lines, start=1):
            parts = line.split()
            if len(parts) != 5:
                self.log_error(f"{label_path}:{l_idx}: Expected exactly 5 fields (cls x y w h), got {len(parts)}: '{line}'")
                continue

            cls_str, x_str, y_str, w_str, h_str = parts
            try:
                cls_id = int(cls_str)
                xc = float(x_str)
                yc = float(y_str)
                w = float(w_str)
                h = float(h_str)
            except ValueError:
                self.log_error(f"{label_path}:{l_idx}: Non-numeric values in line: '{line}'")
                continue

            # Strict finite checks: no NaN, no Inf
            for val_name, val in [("xc", xc), ("yc", yc), ("w", w), ("h", h)]:
                if not math.isfinite(val):
                    self.log_error(f"{label_path}:{l_idx}: Non-finite value ({val_name}={val}) in line: '{line}'")

            if cls_id != 0:
                self.log_error(f"{label_path}:{l_idx}: Invalid class_id {cls_id}. Phone dataset must strictly use class 0.")

            # Center coordinates: 0 <= xc <= 1, 0 <= yc <= 1
            if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0):
                self.log_error(f"{label_path}:{l_idx}: Center coords out of bounds [0, 1]: ({xc}, {yc})")

            # Dimensions: 0 < w <= 1, 0 < h <= 1
            if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                self.log_error(f"{label_path}:{l_idx}: Width/height out of bounds (0, 1]: (w={w}, h={h})")

            x1 = xc - w / 2.0
            x2 = xc + w / 2.0
            y1 = yc - h / 2.0
            y2 = yc + h / 2.0

            # Strict bounding box boundaries [0, 1] without tolerance
            eps = 1e-7
            if x1 < -eps or y1 < -eps or x2 > 1.0 + eps or y2 > 1.0 + eps:
                self.log_error(
                    f"{label_path}:{l_idx}: Bounding box exceeds image boundaries [0, 1]: "
                    f"[{x1:.4f}, {y1:.4f}, {x2:.4f}, {y2:.4f}]"
                )

    def validate_posture_dataset(self) -> Dict[str, Any]:
        posture_stats: Dict[str, Any] = {
            "events_count": 0,
            "behavior_counts": {},
            "splits": {},
            "leakage_checks": {
                "video_leakage": False
            }
        }
        if not self.posture_dir or not os.path.exists(self.posture_dir):
            self.log_warning(f"Posture dataset directory not found: {self.posture_dir}")
            return posture_stats

        # 1. Load session metadata to verify video durations
        video_durations: Dict[str, float] = {}
        sessions_csv = os.path.join(self.posture_dir, "metadata", "sessions.csv")
        if os.path.exists(sessions_csv):
            with open(sessions_csv, "r", encoding="utf-8") as f:
                s_reader = csv.DictReader(f)
                for s_row in s_reader:
                    vid = s_row.get("video_id", "").strip()
                    dur_str = s_row.get("duration_seconds", "").strip()
                    if vid and dur_str:
                        try:
                            video_durations[vid] = float(dur_str)
                        except ValueError:
                            pass

        events_csv = os.path.join(self.posture_dir, "annotations", "events.csv")
        if not os.path.exists(events_csv):
            self.log_error(f"Missing posture events metadata: {events_csv}")
            return posture_stats

        with open(events_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            
            # Canonical check: accept target_id_anonymous or subject_id_anonymous
            effective_headers = set(header)
            if "subject_id_anonymous" in effective_headers:
                effective_headers.add("target_id_anonymous")
            missing_cols = [c for c in REQUIRED_EVENT_COLUMNS if c not in effective_headers]
            if missing_cols:
                self.log_error(f"events.csv missing required columns: {missing_cols}")
                return posture_stats

            seen_event_ids: Set[str] = set()
            vid_to_splits: Dict[str, Set[str]] = {}
            count = 0
            for idx, row in enumerate(reader, start=2):
                count += 1
                ev_id = row.get("event_id", "").strip()
                vid = row.get("video_id", "").strip()
                split = row.get("split", "").strip().lower()
                behavior = row.get("behavior", "").strip().upper()
                start_s_str = row.get("start_seconds", "").strip()
                end_s_str = row.get("end_seconds", "").strip()
                severity = row.get("severity", "").strip().upper()
                review_status = row.get("review_status", "").strip().upper()

                if not ev_id:
                    self.log_error(f"Row {idx}: event_id is empty.")
                elif ev_id in seen_event_ids:
                    self.log_error(f"Row {idx}: Duplicate event_id '{ev_id}'.")
                else:
                    seen_event_ids.add(ev_id)

                if split not in VALID_SPLITS:
                    self.log_error(f"Row {idx}: Invalid split '{split}'. Must be one of {VALID_SPLITS}")
                    continue

                if behavior not in VALID_BEHAVIORS:
                    self.log_error(f"Row {idx}: Invalid behavior '{behavior}'. Must strictly be one of {VALID_BEHAVIORS}")
                    continue

                if review_status and review_status not in VALID_REVIEW_STATUSES:
                    self.log_error(f"Row {idx}: Invalid review_status '{review_status}'. Must be one of {VALID_REVIEW_STATUSES}")

                posture_stats["splits"][split] = posture_stats["splits"].get(split, 0) + 1
                posture_stats["behavior_counts"][behavior] = posture_stats["behavior_counts"].get(behavior, 0) + 1

                try:
                    start_s = float(start_s_str)
                    end_s = float(end_s_str)
                    if not (math.isfinite(start_s) and math.isfinite(end_s)):
                        self.log_error(f"Row {idx}: Non-finite interval start={start_s_str}, end={end_s_str}")
                    elif start_s < 0 or end_s <= start_s:
                        self.log_error(f"Row {idx}: Invalid interval: start={start_s}s must be < end={end_s}s and >= 0")
                    else:
                        dur = end_s - start_s
                        # Check against video duration
                        if vid in video_durations:
                            v_dur = video_durations[vid]
                            if end_s > v_dur + 1e-4:
                                self.log_error(
                                    f"Row {idx}: Event interval end {end_s:.2f}s exceeds video duration {v_dur:.2f}s for video '{vid}'"
                                )

                        # Severity derived check if present
                        if severity:
                            expected_sev = "RED" if dur >= 1.25 else "YELLOW"
                            if severity != expected_sev:
                                self.log_error(
                                    f"Row {idx}: Severity mismatch. Duration is {dur:.2f}s (expected {expected_sev}), but marked as '{severity}'"
                                )
                except ValueError:
                    self.log_error(f"Row {idx}: Non-numeric interval start='{start_s_str}', end='{end_s_str}'")

                if vid:
                    vid_to_splits.setdefault(vid, set()).add(split)

            posture_stats["events_count"] = count

            for vid, sps in vid_to_splits.items():
                if len(sps) > 1:
                    self.log_error(f"POSTURE VIDEO LEAKAGE: video_id '{vid}' appears in multiple splits: {sps}")
                    posture_stats["leakage_checks"]["video_leakage"] = True

        return posture_stats

    def run_validation(self) -> bool:
        self.errors.clear()
        self.warnings.clear()
        phone_res = self.validate_phone_dataset() if self.phone_dir else {}
        posture_res = self.validate_posture_dataset() if self.posture_dir else {}

        self.stats = {
            "phone": phone_res,
            "posture": posture_res,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "passed": len(self.errors) == 0
        }
        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Dataset Protocol & Zero-Leakage Validator (Sprint 2.1A)")
    parser.add_argument("--phone-dir", type=str, default="datasets/phone", help="Path to phone dataset directory")
    parser.add_argument("--posture-dir", type=str, default="datasets/posture", help="Path to posture dataset directory")
    parser.add_argument("--strict", action="store_true", help="Fail if any warning is generated")
    args = parser.parse_args()

    validator = DatasetValidator(phone_dir=args.phone_dir, posture_dir=args.posture_dir)
    passed = validator.run_validation()

    print("================================================================================")
    print("DATASET ZERO-LEAKAGE & PROTOCOL VALIDATION REPORT")
    print("================================================================================")
    print(f"Errors count:   {len(validator.errors)}")
    print(f"Warnings count: {len(validator.warnings)}")

    if validator.errors:
        print("\n[ERRORS DETECTED]")
        for e in validator.errors:
            print(f"  - [FAIL] {e}")

    if validator.warnings:
        print("\n[WARNINGS]")
        for w in validator.warnings:
            print(f"  - [WARN] {w}")

    if passed and (not args.strict or len(validator.warnings) == 0):
        print("\n[PASS] All dataset schemas and zero-leakage invariant checks PASSED.")
        sys.exit(0)
    else:
        print("\n[FAIL] Validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
