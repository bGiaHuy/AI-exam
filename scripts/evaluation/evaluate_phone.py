"""
================================================================================
PHONE DETECTION REPRODUCIBLE EVALUATION HARNESS (SPRINT 2.1A)
================================================================================
Evaluates YOLO Phone Detection models strictly in read-only mode on holdout test set.
Decouples:
1. Ranking Metrics:
   - AP@0.50, mAP@0.50:0.95, and 101-point interpolated Precision-Recall curve
   - Evaluated across all detections down to confidence floor (default 0.001)
2. Operational Metrics:
   - Evaluated strictly at deployment operating point (default conf=0.35, iou=0.50)
   - TP, FP, FN, Precision, Recall, F1
   - False Positives on distractors/hard-negatives, False Alerts per 100 negative images
- Subgroup breakdowns: lighting, occlusion, distance, distractors, bbox scale
- Exports: JSON summary, predictions CSV, PR-curve, FP/FN review lists
- Generates Version Manifest for full traceability
================================================================================
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional

import cv2
import numpy as np

# Add scripts directory to path for version_manifest import
SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from evaluation.version_manifest import create_version_manifest


def box_iou(box1: List[float], box2: List[float]) -> float:
    """
    Computes IoU between two bounding boxes in [x1, y1, x2, y2] format.
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    area2 = max(0.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union = area1 + area2 - inter_area

    if union <= 1e-9:
        return 0.0
    return inter_area / union


def compute_coco_ap(recalls: List[float], precisions: List[float]) -> float:
    """
    Standard 101-point interpolated Average Precision (COCO metric).
    Recalls and Precisions evaluated on sorted predictions.
    """
    if not recalls or not precisions:
        return 0.0

    mrec = np.concatenate(([0.0], recalls, [1.0]))
    mpre = np.concatenate(([0.0], precisions, [0.0]))

    # Precision envelope (monotonically non-increasing backwards)
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])

    # 101-point recall levels: 0.0, 0.01, ..., 1.00
    recall_levels = np.linspace(0.0, 1.0, 101)
    p_interp = []
    for r in recall_levels:
        idx = np.searchsorted(mrec, r, side="left")
        p_interp.append(mpre[idx] if idx < len(mpre) else 0.0)

    return float(np.mean(p_interp))


def evaluate_ap_at_iou(
    all_predictions_sorted: List[Dict[str, Any]],
    gt_boxes_by_sample: Dict[str, List[List[float]]],
    total_gt_boxes: int,
    iou_thresh: float
) -> Tuple[float, List[float], List[float]]:
    """
    Evaluates 1-to-1 matching and computes AP at a specific IoU threshold.
    all_predictions_sorted must be sorted by confidence descending.
    """
    if total_gt_boxes == 0:
        return 0.0, [], []

    matched_gt: Dict[str, Set[int]] = {sid: set() for sid in gt_boxes_by_sample}
    acc_tp = 0
    acc_fp = 0
    recalls = []
    precisions = []

    for p in all_predictions_sorted:
        sid = p["sample_id"]
        box = p["box"]
        sample_gts = gt_boxes_by_sample.get(sid, [])

        best_iou = 0.0
        best_g_idx = -1
        for g_idx, g in enumerate(sample_gts):
            if g_idx in matched_gt[sid]:
                continue
            iou = box_iou(box, g)
            if iou > best_iou:
                best_iou = iou
                best_g_idx = g_idx

        if best_iou >= iou_thresh and best_g_idx >= 0:
            matched_gt[sid].add(best_g_idx)
            acc_tp += 1
        else:
            acc_fp += 1

        rec = acc_tp / total_gt_boxes
        prec = acc_tp / (acc_tp + acc_fp)
        recalls.append(rec)
        precisions.append(prec)

    ap = compute_coco_ap(recalls, precisions)
    return ap, recalls, precisions


class PhoneEvaluationHarness:
    def __init__(
        self,
        weights_path: str,
        dataset_dir: str,
        split: str = "test",
        conf_thresh: float = 0.35,
        iou_thresh: float = 0.50,
        conf_floor: float = 0.001,
        imgsz: int = 960,
        device: str = "cpu"
    ):
        self.weights_path = weights_path
        self.dataset_dir = dataset_dir
        self.split = split.lower()
        self.conf_thresh = conf_thresh      # Operational threshold
        self.iou_thresh = iou_thresh        # Operational IoU matching threshold
        self.conf_floor = conf_floor        # Low confidence floor for ranking / AP
        self.imgsz = imgsz
        self.device = device
        self.model = None

    def load_model(self):
        if not os.path.exists(self.weights_path):
            raise FileNotFoundError(f"Model weights not found: {self.weights_path}")
        from ultralytics import YOLO
        self.model = YOLO(self.weights_path)

    def load_dataset_samples(self) -> List[Dict[str, Any]]:
        samples_csv = os.path.join(self.dataset_dir, "metadata", "samples.csv")
        if not os.path.exists(samples_csv):
            return []

        selected = []
        with open(samples_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("split", "").strip().lower() == self.split:
                    selected.append(row)
        return selected

    def load_ground_truth(self, sample_rel_path: str, img_w: int, img_h: int) -> List[List[float]]:
        base = os.path.splitext(os.path.basename(sample_rel_path))[0]
        label_file = os.path.join(self.dataset_dir, "labels", self.split, f"{base}.txt")
        gt_boxes = []
        if not os.path.exists(label_file):
            return gt_boxes

        with open(label_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    cls_id, xc, yc, w, h = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    if cls_id == 0:
                        x1 = (xc - w / 2.0) * img_w
                        y1 = (yc - h / 2.0) * img_h
                        x2 = (xc + w / 2.0) * img_w
                        y2 = (yc + h / 2.0) * img_h
                        gt_boxes.append([x1, y1, x2, y2])
        return gt_boxes

    def evaluate_predictions(
        self,
        dataset_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Pure evaluation engine:
        Processes a list of samples with their GT and predictions down to conf_floor.
        Strictly decouples:
        1. Ranking metrics (AP@0.5, mAP@0.5:0.95, PR curve) on all predictions >= conf_floor.
        2. Operational metrics (TP, FP, FN, Precision, Recall, F1, false alert rates) at conf_thresh.
        """
        gt_by_sample: Dict[str, List[List[float]]] = {}
        all_preds_ranking: List[Dict[str, Any]] = []
        total_gt_count = 0
        total_negative_samples = 0
        total_distractor_samples = 0

        subgroups = {
            "scale": {"small": {"gt": 0, "tp": 0}, "medium": {"gt": 0, "tp": 0}, "large": {"gt": 0, "tp": 0}},
            "distractors": {"total_distractor_images": 0, "fp_on_distractors": 0}
        }

        # Step 1: Collect GT and Predictions
        for record in dataset_records:
            sid = record["sample_id"]
            gt_boxes = record.get("gt_boxes", [])
            pred_boxes = record.get("pred_boxes", [])  # list of [x1, y1, x2, y2, conf]
            meta = record.get("metadata", {})

            has_phone = meta.get("has_phone", len(gt_boxes) > 0)
            if isinstance(has_phone, str):
                has_phone = has_phone.strip().lower() in ("true", "1", "yes")

            has_distractor = meta.get("has_distractor", meta.get("has_hard_negative", False))
            if isinstance(has_distractor, str):
                has_distractor = has_distractor.strip().lower() in ("true", "1", "yes")

            if not has_phone:
                total_negative_samples += 1
            if has_distractor:
                total_distractor_samples += 1
                subgroups["distractors"]["total_distractor_images"] += 1

            gt_by_sample[sid] = gt_boxes
            total_gt_count += len(gt_boxes)

            # Record scale of GT boxes
            for gx1, gy1, gx2, gy2 in gt_boxes:
                area = (gx2 - gx1) * (gy2 - gy1)
                scale_cat = "small" if area < (32 * 32) else ("medium" if area <= (96 * 96) else "large")
                subgroups["scale"][scale_cat]["gt"] += 1

            for p in pred_boxes:
                px1, py1, px2, py2, pconf = p[0], p[1], p[2], p[3], float(p[4])
                if pconf >= self.conf_floor:
                    all_preds_ranking.append({
                        "sample_id": sid,
                        "box": [px1, py1, px2, py2],
                        "conf": pconf,
                        "metadata": meta
                    })

        # Step 2: RANKING METRICS (Sweep across all predictions >= conf_floor)
        all_preds_ranking.sort(key=lambda x: x["conf"], reverse=True)

        ap_50, recalls_50, precisions_50 = evaluate_ap_at_iou(
            all_preds_ranking, gt_by_sample, total_gt_count, 0.50
        )

        # mAP @ 0.50:0.95
        iou_thresholds = np.linspace(0.50, 0.95, 10)
        aps_50_95 = []
        for iou_t in iou_thresholds:
            ap_val, _, _ = evaluate_ap_at_iou(all_preds_ranking, gt_by_sample, total_gt_count, float(iou_t))
            aps_50_95.append(ap_val)
        map_50_95 = float(np.mean(aps_50_95)) if aps_50_95 else 0.0

        # PR curve samples
        pr_curve = []
        for p_item, r_val, prec_val in zip(all_preds_ranking, recalls_50, precisions_50):
            pr_curve.append({
                "conf": round(p_item["conf"], 4),
                "precision": round(prec_val, 4),
                "recall": round(r_val, 4)
            })

        # Step 3: OPERATIONAL METRICS (Evaluated strictly at conf_thresh, default 0.35)
        op_tp = 0
        op_fp = 0
        op_fn = 0
        fp_on_distractors = 0
        fp_on_negative_images = 0
        fp_review_list = []
        fn_review_list = []
        predictions_rows = []

        for record in dataset_records:
            sid = record["sample_id"]
            gt_boxes = record.get("gt_boxes", [])
            pred_boxes = record.get("pred_boxes", [])
            meta = record.get("metadata", {})

            has_phone = meta.get("has_phone", len(gt_boxes) > 0)
            if isinstance(has_phone, str):
                has_phone = has_phone.strip().lower() in ("true", "1", "yes")

            has_distractor = meta.get("has_distractor", meta.get("has_hard_negative", False))
            if isinstance(has_distractor, str):
                has_distractor = has_distractor.strip().lower() in ("true", "1", "yes")

            # Filter predictions strictly by deployment threshold
            op_preds = [p for p in pred_boxes if float(p[4]) >= self.conf_thresh]
            op_preds.sort(key=lambda p: float(p[4]), reverse=True)

            matched_gt_indices = set()
            sample_fp_count = 0

            for p in op_preds:
                px1, py1, px2, py2, pconf = p[0], p[1], p[2], p[3], float(p[4])
                best_iou = 0.0
                best_g_idx = -1
                for g_idx, g in enumerate(gt_boxes):
                    if g_idx in matched_gt_indices:
                        continue
                    iou = box_iou([px1, py1, px2, py2], g)
                    if iou > best_iou:
                        best_iou = iou
                        best_g_idx = g_idx

                if best_iou >= self.iou_thresh and best_g_idx >= 0:
                    matched_gt_indices.add(best_g_idx)
                    op_tp += 1
                    is_tp = True
                    gx1, gy1, gx2, gy2 = gt_boxes[best_g_idx]
                    area = (gx2 - gx1) * (gy2 - gy1)
                    scale_cat = "small" if area < (32 * 32) else ("medium" if area <= (96 * 96) else "large")
                    subgroups["scale"][scale_cat]["tp"] += 1
                else:
                    op_fp += 1
                    sample_fp_count += 1
                    is_tp = False
                    fp_review_list.append({
                        "sample_id": sid,
                        "pred_box": [px1, py1, px2, py2],
                        "confidence": pconf,
                        "highest_iou": round(best_iou, 4),
                        "metadata": meta
                    })

                predictions_rows.append({
                    "sample_id": sid,
                    "conf": round(pconf, 4),
                    "is_tp": is_tp,
                    "iou": round(best_iou, 4),
                    "bbox": f"[{px1:.1f}, {py1:.1f}, {px2:.1f}, {py2:.1f}]"
                })

            sample_fn = len(gt_boxes) - len(matched_gt_indices)
            op_fn += sample_fn
            for g_idx, g in enumerate(gt_boxes):
                if g_idx not in matched_gt_indices:
                    fn_review_list.append({
                        "sample_id": sid,
                        "gt_box": g,
                        "metadata": meta
                    })

            if not has_phone and sample_fp_count > 0:
                fp_on_negative_images += sample_fp_count
            if not has_phone and has_distractor and sample_fp_count > 0:
                fp_on_distractors += sample_fp_count

        subgroups["distractors"]["fp_on_distractors"] = fp_on_distractors

        op_precision = op_tp / (op_tp + op_fp) if (op_tp + op_fp) > 0 else 0.0
        op_recall = op_tp / total_gt_count if total_gt_count > 0 else 0.0
        op_f1 = (2 * op_precision * op_recall) / (op_precision + op_recall) if (op_precision + op_recall) > 0 else 0.0

        false_alerts_per_negative = (
            fp_on_negative_images / total_negative_samples if total_negative_samples > 0 else 0.0
        )
        false_alerts_per_100_negatives = false_alerts_per_negative * 100.0

        return {
            "evaluation_split": self.split,
            "total_samples": len(dataset_records),
            "total_ground_truth_phones": total_gt_count,
            "total_predictions_ranking": len(all_preds_ranking),
            "ranking_metrics": {
                "conf_floor": self.conf_floor,
                "ap_50": round(ap_50, 4),
                "map_50_95": round(map_50_95, 4),
                "pr_curve_sampled": pr_curve[:100]
            },
            "operational_metrics": {
                "conf_threshold": self.conf_thresh,
                "iou_threshold": self.iou_thresh,
                "tp": op_tp,
                "fp": op_fp,
                "fn": op_fn,
                "precision": round(op_precision, 4),
                "recall": round(op_recall, 4),
                "f1_score": round(op_f1, 4),
                "total_negative_samples": total_negative_samples,
                "false_positives_on_distractors": fp_on_distractors,
                "false_alerts_per_negative_image": round(false_alerts_per_negative, 4),
                "false_alerts_per_100_negative_images": round(false_alerts_per_100_negatives, 2)
            },
            "subgroups": subgroups,
            "predictions_detail": predictions_rows,
            "false_positives_review": fp_review_list,
            "false_negatives_review": fn_review_list
        }

    def run(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        out_dir = output_dir or "data/benchmark_reports/phone_eval"
        os.makedirs(out_dir, exist_ok=True)

        samples = self.load_dataset_samples()
        if not samples:
            print(f"[WARN] No samples found in '{self.dataset_dir}' for split='{self.split}'.")
            empty_summary = {
                "status": "BLOCKED",
                "reason": f"No samples found in split '{self.split}'",
                "split": self.split,
                "manifest": create_version_manifest(
                    weights_path=self.weights_path,
                    dataset_dir=self.dataset_dir,
                    dataset_metadata_path=os.path.join(self.dataset_dir, "metadata", "samples.csv"),
                    split=self.split
                )
            }
            summary_path = os.path.join(out_dir, "phone_eval_summary.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(empty_summary, f, indent=2)
            return empty_summary

        self.load_model()
        records = []
        for s in samples:
            rel_path = s["relative_path"]
            img_full = os.path.join(self.dataset_dir, rel_path)
            if not os.path.exists(img_full):
                continue
            img = cv2.imread(img_full)
            if img is None:
                continue
            h, w = img.shape[:2]
            gt_boxes = self.load_ground_truth(rel_path, w, h)

            # Inference with low confidence floor for ranking sweep
            res = self.model(img, conf=self.conf_floor, imgsz=self.imgsz, device=self.device, verbose=False)[0]
            pred_boxes = []
            for b in res.boxes:
                bx = b.xyxy[0].tolist()
                c = float(b.conf[0])
                pred_boxes.append([bx[0], bx[1], bx[2], bx[3], c])

            records.append({
                "sample_id": s["sample_id"],
                "gt_boxes": gt_boxes,
                "pred_boxes": pred_boxes,
                "metadata": s
            })

        results = self.evaluate_predictions(records)
        manifest = create_version_manifest(
            weights_path=self.weights_path,
            dataset_dir=self.dataset_dir,
            dataset_metadata_path=os.path.join(self.dataset_dir, "metadata", "samples.csv"),
            split=self.split,
            config={
                "conf_thresh": self.conf_thresh,
                "iou_thresh": self.iou_thresh,
                "conf_floor": self.conf_floor,
                "imgsz": self.imgsz,
                "split": self.split
            }
        )
        results["version_manifest"] = manifest

        # Save artifacts
        summary_path = os.path.join(out_dir, f"phone_eval_{self.split}_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        pred_csv_path = os.path.join(out_dir, f"phone_eval_{self.split}_predictions.csv")
        with open(pred_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "conf", "is_tp", "iou", "bbox"])
            writer.writeheader()
            for r in results["predictions_detail"]:
                writer.writerow(r)

        print(f"[OK] Phone evaluation completed. Summary saved: {summary_path}")
        return results


def main():
    parser = argparse.ArgumentParser(description="Reproducible Phone Detection Evaluation Harness (Sprint 2.1A)")
    parser.add_argument("--weights", type=str, default="model/weights/phone_detector_v5.pt", help="Path to weights file")
    parser.add_argument("--dataset-dir", type=str, default="datasets/phone", help="Path to phone dataset")
    parser.add_argument("--split", type=str, default="test", help="Split to evaluate: test | val | train")
    parser.add_argument("--conf-thresh", type=float, default=0.35, help="Deployment operational confidence threshold")
    parser.add_argument("--iou-thresh", type=float, default=0.50, help="IoU threshold for TP matching")
    parser.add_argument("--conf-floor", type=float, default=0.001, help="Low confidence floor for ranking evaluation")
    parser.add_argument("--imgsz", type=int, default=960, help="Inference image resolution")
    parser.add_argument("--output-dir", type=str, default="data/benchmark_reports/phone_eval", help="Directory to save evaluation reports")
    args = parser.parse_args()

    harness = PhoneEvaluationHarness(
        weights_path=args.weights,
        dataset_dir=args.dataset_dir,
        split=args.split,
        conf_thresh=args.conf_thresh,
        iou_thresh=args.iou_thresh,
        conf_floor=args.conf_floor,
        imgsz=args.imgsz
    )
    res = harness.run(output_dir=args.output_dir)
    print("\n--- RANKING METRICS ---")
    print(json.dumps(res.get("ranking_metrics", {}), indent=2))
    print("\n--- OPERATIONAL METRICS (at conf=0.35) ---")
    print(json.dumps(res.get("operational_metrics", {}), indent=2))


if __name__ == "__main__":
    main()
