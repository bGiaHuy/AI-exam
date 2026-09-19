"""
================================================================================
UNIT TESTS & DRY-RUN FIXTURES FOR EVALUATION HARNESS (SPRINT 2.1A)
================================================================================
22 Required Test Cases:
1.  YAML path resolves correctly via Ultralytics resolver (root + subfolder).
2.  Box valid at image edge [0, 1] accepted.
3.  Box exceeding image edge rejected without tolerance.
4.  NaN, Inf, and non-positive width/height rejected.
5.  Phone and distractor simultaneous coexistence accepted.
6.  Negative image with annotation rejected.
7.  Positive image without annotation rejected.
8.  Duplicate sample_id or relative_path rejected.
9.  Orphan image or label file detected and rejected.
10. Leakage detected by video, session, or content hash.
11. Dataset fingerprint changes on image edit.
12. Dataset fingerprint changes on label edit.
13. Dataset fingerprint deterministic and stable when unchanged.
14. AP@0.5 perfect prediction equals 1.0.
15. AP@0.5 strictly drops when high-confidence FP is introduced.
16. Operational metrics at 0.35 strictly decoupled from ranking AP.
17. Event one-to-one matching enforced (no double counting).
18. Excessive duration prediction starting at onset is not TP (tIoU < 0.30).
19. Overlapping ground truth intervals unioned correctly for normal duration.
20. Signed onset error negative values preserved for early alerts.
21. FAR returns 'not_applicable' when normal video duration is zero.
22. Posture event exceeding video duration is rejected.
================================================================================
"""

import os
import sys
import shutil
import tempfile
import unittest
import numpy as np
import cv2

# Add scripts directory and repo root to sys.path
SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_ROOT = os.path.dirname(SCRIPTS_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from evaluation.validate_dataset import DatasetValidator
from evaluation.evaluate_phone import PhoneEvaluationHarness, box_iou, compute_coco_ap
from evaluation.evaluate_posture_events import (
    PostureEventEvaluationHarness,
    temporal_iou,
    compute_union_duration
)
from evaluation.version_manifest import (
    create_version_manifest,
    compute_dataset_fingerprint
)


def create_blank_image(filepath: str, width: int = 100, height: int = 100, color: int = 128):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img = np.full((height, width, 3), color, dtype=np.uint8)
    cv2.imwrite(filepath, img)


class TestEvaluationHarness(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_eval_21a_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. YAML Path Resolves Correctly
    # --------------------------------------------------------------------------
    def test_01_yaml_path_resolves_correctly(self):
        from ultralytics.data.utils import check_det_dataset
        yaml_path = os.path.join(REPO_ROOT, "datasets", "phone", "data_phone.yaml")
        self.assertTrue(os.path.exists(yaml_path), f"YAML file missing: {yaml_path}")

        # Resolve from project root
        res_root = check_det_dataset(yaml_path)
        self.assertTrue(os.path.exists(res_root["train"]), f"Resolved train path does not exist: {res_root['train']}")
        self.assertTrue(os.path.exists(res_root["val"]), f"Resolved val path does not exist: {res_root['val']}")
        self.assertTrue(os.path.exists(res_root["test"]), f"Resolved test path does not exist: {res_root['test']}")
        self.assertTrue(res_root["train"].endswith(os.path.join("images", "train")))

        # Resolve from a different subdirectory (e.g. scripts/evaluation)
        old_cwd = os.getcwd()
        try:
            os.chdir(os.path.join(REPO_ROOT, "scripts", "evaluation"))
            rel_yaml = os.path.relpath(yaml_path, os.getcwd())
            res_sub = check_det_dataset(rel_yaml)
            self.assertTrue(os.path.exists(res_sub["train"]))
            self.assertEqual(res_root["train"], res_sub["train"])
        finally:
            os.chdir(old_cwd)

    # --------------------------------------------------------------------------
    # 2. Box Valid at Edge
    # --------------------------------------------------------------------------
    def test_02_box_valid_at_edge(self):
        phone_dir = os.path.join(self.test_dir, "phone_edge")
        img_rel = "images/train/edge_img.jpg"
        img_full = os.path.join(phone_dir, img_rel)
        create_blank_image(img_full)

        lbl_path = os.path.join(phone_dir, "labels", "train", "edge_img.txt")
        os.makedirs(os.path.dirname(lbl_path), exist_ok=True)
        # Box precisely spanning [0, 1] in both dims: xc=0.5, yc=0.5, w=1.0, h=1.0
        with open(lbl_path, "w") as f:
            f.write("0 0.5 0.5 1.0 1.0\n")

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            f.write(f"s_edge,{img_rel},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,True,False,,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertTrue(passed, f"Valid box at edge was rejected: {validator.errors}")

    # --------------------------------------------------------------------------
    # 3. Box Exceeding Edge Rejected
    # --------------------------------------------------------------------------
    def test_03_box_exceeding_edge_rejected(self):
        phone_dir = os.path.join(self.test_dir, "phone_exceed")
        img_rel = "images/train/exceed.jpg"
        img_full = os.path.join(phone_dir, img_rel)
        create_blank_image(img_full)

        lbl_path = os.path.join(phone_dir, "labels", "train", "exceed.txt")
        os.makedirs(os.path.dirname(lbl_path), exist_ok=True)
        # xc=0.9, w=0.3 -> x2 = 1.05 > 1.0 (exceeds border)
        with open(lbl_path, "w") as f:
            f.write("0 0.9 0.5 0.3 0.3\n")

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            f.write(f"s_exc,{img_rel},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,True,False,,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertFalse(passed)
        self.assertTrue(any("exceeds image boundaries" in e for e in validator.errors))

    # --------------------------------------------------------------------------
    # 4. NaN, Inf, and Non-positive Width/Height Rejected
    # --------------------------------------------------------------------------
    def test_04_nan_inf_zero_wh_rejected(self):
        for bad_line, err_match in [
            ("0 nan 0.5 0.2 0.3", "Non-finite value"),
            ("0 0.5 inf 0.2 0.3", "Non-finite value"),
            ("0 0.5 0.5 0.0 0.3", "Width/height out of bounds"),
            ("0 0.5 0.5 0.2 -0.1", "Width/height out of bounds"),
        ]:
            phone_dir = os.path.join(self.test_dir, f"phone_bad_{bad_line[:8].replace(' ', '_')}")
            img_rel = "images/train/bad.jpg"
            create_blank_image(os.path.join(phone_dir, img_rel))

            lbl_path = os.path.join(phone_dir, "labels", "train", "bad.txt")
            os.makedirs(os.path.dirname(lbl_path), exist_ok=True)
            with open(lbl_path, "w") as f:
                f.write(bad_line + "\n")

            meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
            os.makedirs(os.path.dirname(meta_path), exist_ok=True)
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
                f.write(f"s_bad,{img_rel},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,True,False,,normal,none,close,local,approved\n")

            validator = DatasetValidator(phone_dir=phone_dir)
            passed = validator.run_validation()
            self.assertFalse(passed, f"Failed to reject invalid line: '{bad_line}'")
            self.assertTrue(any(err_match in e for e in validator.errors))

    # --------------------------------------------------------------------------
    # 5. Phone and Distractor Simultaneous Coexistence Accepted
    # --------------------------------------------------------------------------
    def test_05_phone_and_distractor_simultaneous_accepted(self):
        phone_dir = os.path.join(self.test_dir, "phone_both")
        img_rel = "images/train/both.jpg"
        create_blank_image(os.path.join(phone_dir, img_rel))

        lbl_path = os.path.join(phone_dir, "labels", "train", "both.txt")
        os.makedirs(os.path.dirname(lbl_path), exist_ok=True)
        with open(lbl_path, "w") as f:
            f.write("0 0.4 0.4 0.2 0.3\n")  # Phone annotated as class 0

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            # has_phone=True AND has_distractor=True
            f.write(f"s_both,{img_rel},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,True,True,calculator|wallet,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertTrue(passed, f"Both phone and distractor should be valid: {validator.errors}")
        self.assertEqual(validator.stats["phone"]["phones_positive"], 1)
        self.assertEqual(validator.stats["phone"]["distractors"], 1)

    # --------------------------------------------------------------------------
    # 6. Negative with Annotation Rejected
    # --------------------------------------------------------------------------
    def test_06_negative_with_annotation_rejected(self):
        phone_dir = os.path.join(self.test_dir, "phone_neg_annot")
        img_rel = "images/train/neg_annot.jpg"
        create_blank_image(os.path.join(phone_dir, img_rel))

        lbl_path = os.path.join(phone_dir, "labels", "train", "neg_annot.txt")
        os.makedirs(os.path.dirname(lbl_path), exist_ok=True)
        with open(lbl_path, "w") as f:
            f.write("0 0.5 0.5 0.2 0.2\n")  # Should be empty for has_phone=False!

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            f.write(f"s_neg,{img_rel},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,False,True,pencil_case,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertFalse(passed)
        self.assertTrue(any("Negatives must have empty label files" in e for e in validator.errors))

    # --------------------------------------------------------------------------
    # 7. Positive without Annotation Rejected
    # --------------------------------------------------------------------------
    def test_07_positive_without_annotation_rejected(self):
        phone_dir = os.path.join(self.test_dir, "phone_pos_empty")
        img_rel = "images/train/pos_empty.jpg"
        create_blank_image(os.path.join(phone_dir, img_rel))

        lbl_path = os.path.join(phone_dir, "labels", "train", "pos_empty.txt")
        os.makedirs(os.path.dirname(lbl_path), exist_ok=True)
        with open(lbl_path, "w") as f:
            pass  # Empty label for has_phone=True -> INVALID

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            f.write(f"s_pos,{img_rel},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,True,False,,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertFalse(passed)
        self.assertTrue(any("has_phone=True but label file" in e for e in validator.errors))

    # --------------------------------------------------------------------------
    # 8. Duplicate sample_id or path Rejected
    # --------------------------------------------------------------------------
    def test_08_duplicate_sample_id_or_path_rejected(self):
        phone_dir = os.path.join(self.test_dir, "phone_dup")
        img1 = "images/train/img1.jpg"
        img2 = "images/train/img2.jpg"
        create_blank_image(os.path.join(phone_dir, img1))
        create_blank_image(os.path.join(phone_dir, img2))

        for p in ["img1", "img2"]:
            lp = os.path.join(phone_dir, "labels", "train", f"{p}.txt")
            os.makedirs(os.path.dirname(lp), exist_ok=True)
            with open(lp, "w") as f:
                f.write("0 0.5 0.5 0.2 0.2\n")

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        # Duplicate sample_id "s_same"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            f.write(f"s_same,{img1},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,True,False,,normal,none,close,local,approved\n")
            f.write(f"s_same,{img2},vid_1,sess_1,subj_2,scene_1,cam_1,2.0,train,True,False,,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertFalse(passed)
        self.assertTrue(any("Duplicate sample_id" in e for e in validator.errors))

    # --------------------------------------------------------------------------
    # 9. Orphan Image or Label Detected
    # --------------------------------------------------------------------------
    def test_09_orphan_image_or_label_rejected(self):
        phone_dir = os.path.join(self.test_dir, "phone_orphan")
        img1 = "images/train/img1.jpg"
        create_blank_image(os.path.join(phone_dir, img1))

        # Valid registered sample
        lp1 = os.path.join(phone_dir, "labels", "train", "img1.txt")
        os.makedirs(os.path.dirname(lp1), exist_ok=True)
        with open(lp1, "w") as f:
            f.write("0 0.5 0.5 0.2 0.2\n")

        # Create unreferenced orphan label
        lp_orphan = os.path.join(phone_dir, "labels", "train", "orphan_ghost.txt")
        with open(lp_orphan, "w") as f:
            f.write("0 0.5 0.5 0.2 0.2\n")

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            f.write(f"s_1,{img1},vid_1,sess_1,subj_1,scene_1,cam_1,1.0,train,True,False,,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertFalse(passed)
        self.assertTrue(any("Orphan label file" in e for e in validator.errors))

    # --------------------------------------------------------------------------
    # 10. Leakage Detected (Video / Session / Content Hash)
    # --------------------------------------------------------------------------
    def test_10_leakage_detected(self):
        phone_dir = os.path.join(self.test_dir, "phone_leakage")
        img_train = "images/train/t1.jpg"
        img_test = "images/test/t2.jpg"
        # Create identical images to trigger content-hash leakage
        create_blank_image(os.path.join(phone_dir, img_train), color=100)
        create_blank_image(os.path.join(phone_dir, img_test), color=100)

        for p, sp in [("t1", "train"), ("t2", "test")]:
            lp = os.path.join(phone_dir, "labels", sp, f"{p}.txt")
            os.makedirs(os.path.dirname(lp), exist_ok=True)
            with open(lp, "w") as f:
                f.write("0 0.5 0.5 0.2 0.2\n")

        meta_path = os.path.join(phone_dir, "metadata", "samples.csv")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("sample_id,relative_path,source_video_id,session_id,subject_id_anonymous,scene_id,camera_id,timestamp_seconds,split,has_phone,has_distractor,distractor_types,lighting,occlusion,distance_group,source_provenance,usage_permission\n")
            f.write(f"s_tr,{img_train},SHARED_VIDEO,SHARED_SESS,subj_1,scene_1,cam_1,1.0,train,True,False,,normal,none,close,local,approved\n")
            f.write(f"s_te,{img_test},SHARED_VIDEO,SHARED_SESS,subj_2,scene_1,cam_1,2.0,test,True,False,,normal,none,close,local,approved\n")

        validator = DatasetValidator(phone_dir=phone_dir)
        passed = validator.run_validation()
        self.assertFalse(passed)
        self.assertTrue(any("SOURCE VIDEO LEAKAGE" in e for e in validator.errors))
        self.assertTrue(any("SESSION LEAKAGE" in e for e in validator.errors))
        self.assertTrue(any("CONTENT HASH LEAKAGE" in e for e in validator.errors))

    # --------------------------------------------------------------------------
    # 11. Dataset Fingerprint Changes on Image Edit
    # --------------------------------------------------------------------------
    def test_11_dataset_fingerprint_changes_on_image_edit(self):
        d_dir = os.path.join(self.test_dir, "fp_img_test")
        img_p = os.path.join(d_dir, "images", "train", "img.jpg")
        create_blank_image(img_p, color=50)

        fp1 = compute_dataset_fingerprint(d_dir, split="train")

        # Edit image
        create_blank_image(img_p, color=150)
        fp2 = compute_dataset_fingerprint(d_dir, split="train")

        self.assertNotEqual(fp1, fp2, "Fingerprint must change when image bytes are modified.")

    # --------------------------------------------------------------------------
    # 12. Dataset Fingerprint Changes on Label Edit
    # --------------------------------------------------------------------------
    def test_12_dataset_fingerprint_changes_on_label_edit(self):
        d_dir = os.path.join(self.test_dir, "fp_lbl_test")
        lbl_p = os.path.join(d_dir, "labels", "train", "img.txt")
        os.makedirs(os.path.dirname(lbl_p), exist_ok=True)
        with open(lbl_p, "w") as f:
            f.write("0 0.5 0.5 0.2 0.2\n")

        fp1 = compute_dataset_fingerprint(d_dir, split="train")

        # Edit label content
        with open(lbl_p, "w") as f:
            f.write("0 0.6 0.6 0.3 0.3\n")
        fp2 = compute_dataset_fingerprint(d_dir, split="train")

        self.assertNotEqual(fp1, fp2, "Fingerprint must change when label annotations are modified.")

    # --------------------------------------------------------------------------
    # 13. Dataset Fingerprint Stable When Unchanged
    # --------------------------------------------------------------------------
    def test_13_dataset_fingerprint_stable_when_unchanged(self):
        d_dir = os.path.join(self.test_dir, "fp_stable_test")
        img_p = os.path.join(d_dir, "images", "train", "img.jpg")
        create_blank_image(img_p, color=77)

        fp1 = compute_dataset_fingerprint(d_dir, split="train")
        fp2 = compute_dataset_fingerprint(d_dir, split="train")

        self.assertEqual(fp1, fp2, "Fingerprint must be 100% deterministic on unchanged dataset.")

    # --------------------------------------------------------------------------
    # 14. AP Perfect Prediction Equals 1.0
    # --------------------------------------------------------------------------
    def test_14_ap_perfect_prediction_equals_one(self):
        records = [
            {
                "sample_id": "s1",
                "gt_boxes": [[100.0, 100.0, 200.0, 200.0]],
                "pred_boxes": [[100.0, 100.0, 200.0, 200.0, 0.95]],
                "metadata": {"has_phone": True}
            },
            {
                "sample_id": "s2",
                "gt_boxes": [[300.0, 300.0, 400.0, 400.0]],
                "pred_boxes": [[300.0, 300.0, 400.0, 400.0, 0.90]],
                "metadata": {"has_phone": True}
            }
        ]
        harness = PhoneEvaluationHarness(
            weights_path="dummy.pt", dataset_dir="dummy", conf_thresh=0.35, iou_thresh=0.50
        )
        res = harness.evaluate_predictions(records)
        self.assertAlmostEqual(res["ranking_metrics"]["ap_50"], 1.0, places=4)
        self.assertAlmostEqual(res["ranking_metrics"]["map_50_95"], 1.0, places=4)

    # --------------------------------------------------------------------------
    # 15. AP Drops on High-Confidence False Positive
    # --------------------------------------------------------------------------
    def test_15_ap_drops_on_high_conf_false_positive(self):
        # Base records: 1 GT box, 1 TP prediction at conf 0.90
        base_records = [
            {
                "sample_id": "s1",
                "gt_boxes": [[100.0, 100.0, 200.0, 200.0]],
                "pred_boxes": [[100.0, 100.0, 200.0, 200.0, 0.90]],
                "metadata": {"has_phone": True}
            }
        ]
        harness = PhoneEvaluationHarness(
            weights_path="dummy.pt", dataset_dir="dummy", conf_thresh=0.35, iou_thresh=0.50
        )
        base_res = harness.evaluate_predictions(base_records)
        self.assertAlmostEqual(base_res["ranking_metrics"]["ap_50"], 1.0, places=4)

        # Add high-conf FP (conf=0.99) with 0 IoU
        records_with_fp = [
            {
                "sample_id": "s1",
                "gt_boxes": [[100.0, 100.0, 200.0, 200.0]],
                "pred_boxes": [
                    [100.0, 100.0, 200.0, 200.0, 0.90],     # TP
                    [800.0, 800.0, 900.0, 900.0, 0.99]      # FP with higher confidence!
                ],
                "metadata": {"has_phone": True}
            }
        ]
        res_fp = harness.evaluate_predictions(records_with_fp)
        self.assertLess(
            res_fp["ranking_metrics"]["ap_50"],
            base_res["ranking_metrics"]["ap_50"],
            "AP must drop when high-confidence false positive is added."
        )
        self.assertAlmostEqual(res_fp["ranking_metrics"]["ap_50"], 0.50, places=4)

    # --------------------------------------------------------------------------
    # 16. Operational Metrics at 0.35 Decoupled from AP
    # --------------------------------------------------------------------------
    def test_16_operational_metrics_at_035_decoupled_from_ap(self):
        # 1 GT, 1 pred with conf=0.20 (between conf_floor 0.001 and conf_thresh 0.35)
        records = [
            {
                "sample_id": "s1",
                "gt_boxes": [[100.0, 100.0, 200.0, 200.0]],
                "pred_boxes": [[100.0, 100.0, 200.0, 200.0, 0.20]],
                "metadata": {"has_phone": True}
            }
        ]
        harness = PhoneEvaluationHarness(
            weights_path="dummy.pt", dataset_dir="dummy", conf_thresh=0.35, conf_floor=0.001
        )
        res = harness.evaluate_predictions(records)

        # In ranking metrics: prediction is included (conf >= 0.001), achieving AP=1.0
        self.assertEqual(res["total_predictions_ranking"], 1)
        self.assertAlmostEqual(res["ranking_metrics"]["ap_50"], 1.0, places=4)

        # In operational metrics: prediction is filtered out by conf_thresh=0.35 -> TP=0, FN=1
        op = res["operational_metrics"]
        self.assertEqual(op["tp"], 0)
        self.assertEqual(op["fn"], 1)
        self.assertEqual(op["precision"], 0.0)
        self.assertEqual(op["recall"], 0.0)

    # --------------------------------------------------------------------------
    # 17. Event One-to-One Matching
    # --------------------------------------------------------------------------
    def test_17_event_one_to_one_matching(self):
        gt_events = [
            {
                "event_id": "gt_1",
                "video_id": "vid_1",
                "interval": (10.0, 15.0),
                "duration": 5.0,
                "direction": "LEFT"
            }
        ]
        # Two overlapping predictions for the single GT event
        pred_events = [
            {"video_id": "vid_1", "interval": (10.0, 14.5), "confidence": 0.95},
            {"video_id": "vid_1", "interval": (10.5, 15.0), "confidence": 0.85}
        ]
        harness = PostureEventEvaluationHarness(min_tiou=0.30)
        res = harness.match_events(gt_events, pred_events, total_normal_duration_minutes=1.0)
        m = res["metrics"]

        # Strict 1-to-1 matching: exactly 1 TP and 1 FP
        self.assertEqual(m["tp"], 1)
        self.assertEqual(m["fp"], 1)
        self.assertEqual(m["fn"], 0)
        self.assertAlmostEqual(m["event_precision"], 0.50, places=4)
        self.assertAlmostEqual(m["event_recall"], 1.00, places=4)

    # --------------------------------------------------------------------------
    # 18. Excessive Duration Prediction Not TP
    # --------------------------------------------------------------------------
    def test_18_excessive_duration_prediction_not_tp(self):
        gt_events = [
            {
                "event_id": "gt_short",
                "video_id": "vid_1",
                "interval": (10.0, 15.0),  # 5s
                "duration": 5.0,
                "direction": "RIGHT"
            }
        ]
        # Prediction starts on time at 10.0s but drags on for 110 seconds!
        # inter = 5.0s, union = 100.0s -> tIoU = 0.05 < 0.30
        pred_events = [
            {"video_id": "vid_1", "interval": (10.0, 110.0), "confidence": 0.90}
        ]
        harness = PostureEventEvaluationHarness(min_tiou=0.30)
        res = harness.match_events(gt_events, pred_events, total_normal_duration_minutes=2.0)
        m = res["metrics"]

        # Must NOT match because tIoU is only 0.05!
        self.assertEqual(m["tp"], 0, "Excessive duration prediction must not be classified as TP.")
        self.assertEqual(m["fp"], 1)
        self.assertEqual(m["fn"], 1)

    # --------------------------------------------------------------------------
    # 19. Overlapping GT Intervals Union Correctly
    # --------------------------------------------------------------------------
    def test_19_overlapping_gt_intervals_union_correctly(self):
        # [10, 20] (10s) and [15, 25] (10s) overlap by 5s -> union = [10, 25] (15s)
        # plus disjoint [30, 35] (5s) -> total = 20.0s
        intervals = [(10.0, 20.0), (15.0, 25.0), (30.0, 35.0)]
        union_dur = compute_union_duration(intervals)
        self.assertAlmostEqual(union_dur, 20.0, places=4)

    # --------------------------------------------------------------------------
    # 20. Signed Onset Error Negative Preserved for Early Alerts
    # --------------------------------------------------------------------------
    def test_20_signed_onset_error_negative_preserved(self):
        gt_events = [
            {
                "event_id": "gt_early",
                "video_id": "vid_1",
                "interval": (10.0, 15.0),
                "duration": 5.0,
                "direction": "LEFT"
            }
        ]
        # Prediction triggers at 9.2s (0.8s earlier than GT)
        # inter=[10.0, 14.8]=4.8s, union=[9.2, 15.0]=5.8s -> tIoU = 0.828 >= 0.30
        pred_events = [
            {"video_id": "vid_1", "interval": (9.2, 14.8), "confidence": 0.92}
        ]
        harness = PostureEventEvaluationHarness(min_tiou=0.30)
        res = harness.match_events(gt_events, pred_events, total_normal_duration_minutes=1.0)
        m = res["metrics"]

        self.assertEqual(m["tp"], 1)
        self.assertEqual(m["early_alert_count"], 1)
        self.assertAlmostEqual(m["early_alert_rate"], 1.0, places=4)
        self.assertAlmostEqual(m["signed_onset_error"]["mean"], -0.8000, places=4)
        # Detection delay should clamp to 0 for early alerts
        self.assertAlmostEqual(m["detection_delay"]["mean"], 0.0000, places=4)

    # --------------------------------------------------------------------------
    # 21. FAR with Zero Normal Duration Returns 'not_applicable'
    # --------------------------------------------------------------------------
    def test_21_far_with_zero_normal_duration_returns_not_applicable(self):
        gt_events = [
            {
                "event_id": "gt_full",
                "video_id": "vid_full",
                "interval": (0.0, 60.0),
                "duration": 60.0,
                "direction": "LEFT"
            }
        ]
        pred_events = [
            {"video_id": "vid_full", "interval": (10.0, 20.0), "confidence": 0.80}
        ]
        # Video is 60s, cheating covers 60s -> normal duration is 0s
        video_durations = {"vid_full": 60.0}
        harness = PostureEventEvaluationHarness(min_tiou=0.30)
        res = harness.match_events(gt_events, pred_events, video_durations=video_durations)
        m = res["metrics"]

        self.assertEqual(
            m["false_alerts_per_minute_normal"],
            "not_applicable",
            "FAR must return 'not_applicable' when normal video duration is 0."
        )

    # --------------------------------------------------------------------------
    # 22. Event Exceeding Video Duration Rejected
    # --------------------------------------------------------------------------
    def test_22_event_exceeding_video_duration_rejected(self):
        posture_dir = os.path.join(self.test_dir, "posture_exceed")
        os.makedirs(os.path.join(posture_dir, "metadata"), exist_ok=True)
        os.makedirs(os.path.join(posture_dir, "annotations"), exist_ok=True)

        # Video duration is 30.0s
        sessions_csv = os.path.join(posture_dir, "metadata", "sessions.csv")
        with open(sessions_csv, "w", encoding="utf-8") as f:
            f.write("session_id,video_id,scene_id,camera_id,duration_seconds,fps,split,total_events,description\n")
            f.write("s_1,v_short,sc_1,c_1,30.0,30,train,1,test session\n")

        # Event ends at 35.0s > 30.0s video duration!
        events_csv = os.path.join(posture_dir, "annotations", "events.csv")
        with open(events_csv, "w", encoding="utf-8") as f:
            f.write("event_id,video_id,target_id_anonymous,scene_id,behavior,start_seconds,end_seconds,direction,severity,annotator,review_status,split\n")
            f.write("ev_1,v_short,tgt_1,sc_1,HEAD_TURNING,10.0,35.0,LEFT,RED,ann_1,APPROVED,train\n")

        validator = DatasetValidator(posture_dir=posture_dir)
        passed = validator.run_validation()
        self.assertFalse(passed)
        self.assertTrue(any("exceeds video duration 30.00s" in e for e in validator.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
