"""
================================================================================
HEAD-TURNING EVENT-LEVEL REPRODUCIBLE EVALUATION HARNESS (SPRINT 2.1A)
================================================================================
Evaluates head-turning cheating detection at the EVENT level (not single frame):
- Temporal IoU (tIoU) matching with strict 1-to-1 bipartite/greedy assignment.
- Decouples warning policy (derived from 1.25s threshold) from ground truth.
- Signed onset error (preserves negative values for early alerts).
- False alert rate per minute of normal video duration (using union of GT intervals).
- Returns 'not_applicable' when normal video duration is 0.
- Subgroup breakdown: direction (LEFT/RIGHT/OTHER), duration group (<2s, >=2s).
================================================================================
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional, Union

import numpy as np

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from evaluation.version_manifest import create_version_manifest


def temporal_iou(interval_a: Tuple[float, float], interval_b: Tuple[float, float]) -> float:
    """
    Computes 1D Temporal IoU between two time intervals [start, end].
    """
    start_a, end_a = interval_a
    start_b, end_b = interval_b

    inter_start = max(start_a, start_b)
    inter_end = min(end_a, end_b)
    inter_len = max(0.0, inter_end - inter_start)

    union_start = min(start_a, start_b)
    union_end = max(end_a, end_b)
    union_len = union_end - union_start

    if union_len <= 1e-9:
        return 0.0
    return inter_len / union_len


def compute_union_duration(intervals: List[Tuple[float, float]]) -> float:
    """
    Computes the total duration of the union of intervals, correctly handling overlaps.
    """
    if not intervals:
        return 0.0
    valid_intervals = [
        (float(s), float(e)) for s, e in intervals if e > s and s >= 0
    ]
    if not valid_intervals:
        return 0.0

    sorted_intervals = sorted(valid_intervals, key=lambda x: x[0])
    merged = []
    curr_s, curr_e = sorted_intervals[0]

    for s, e in sorted_intervals[1:]:
        if s <= curr_e:
            curr_e = max(curr_e, e)
        else:
            merged.append((curr_s, curr_e))
            curr_s, curr_e = s, e
    merged.append((curr_s, curr_e))

    return sum(e - s for s, e in merged)


class PostureEventEvaluationHarness:
    def __init__(
        self,
        dataset_dir: str = "datasets/posture",
        split: str = "test",
        min_tiou: float = 0.30,
        onset_tolerance_sec: float = 0.75,
        red_duration_thresh: float = 1.25
    ):
        self.dataset_dir = dataset_dir
        self.split = split.lower()
        self.min_tiou = min_tiou
        self.onset_tolerance_sec = onset_tolerance_sec
        self.red_duration_thresh = red_duration_thresh

    def load_ground_truth_events(self) -> List[Dict[str, Any]]:
        events_csv = os.path.join(self.dataset_dir, "annotations", "events.csv")
        if not os.path.exists(events_csv):
            return []

        gt_events = []
        with open(events_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("split", "").strip().lower() != self.split:
                    continue
                behavior = row.get("behavior", "").strip().upper()
                if behavior != "HEAD_TURNING":
                    continue
                review = row.get("review_status", "APPROVED").strip().upper()
                if review == "REJECTED":
                    continue

                try:
                    start_s = float(row.get("start_seconds", 0.0))
                    end_s = float(row.get("end_seconds", 0.0))
                    dur = end_s - start_s
                    # Policy G: Derive severity from duration threshold
                    derived_severity = "RED" if dur >= self.red_duration_thresh else "YELLOW"

                    target_id = row.get("target_id_anonymous") or row.get("subject_id_anonymous") or ""
                    gt_events.append({
                        "event_id": row.get("event_id", ""),
                        "video_id": row.get("video_id", ""),
                        "target_id_anonymous": target_id.strip(),
                        "interval": (start_s, end_s),
                        "duration": dur,
                        "direction": row.get("direction", "NONE").upper(),
                        "severity": derived_severity,
                        "review_status": review,
                        "raw_row": row
                    })
                except ValueError:
                    continue
        return gt_events

    def load_session_metadata(self) -> Dict[str, Dict[str, Any]]:
        sessions_csv = os.path.join(self.dataset_dir, "metadata", "sessions.csv")
        sessions = {}
        if not os.path.exists(sessions_csv):
            return sessions

        with open(sessions_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vid = row.get("video_id", "")
                if vid:
                    sessions[vid] = row
        return sessions

    def match_events(
        self,
        gt_events: List[Dict[str, Any]],
        pred_events: List[Dict[str, Any]],
        video_durations: Optional[Dict[str, float]] = None,
        total_normal_duration_minutes: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Pure matching engine:
        - Strict 1-to-1 matching based on primary criterion: tIoU >= min_tiou (0.30).
        - Computes signed onset error (pred_start - gt_start).
        - Computes positive detection delay max(0, signed_onset_error).
        - Reports early alert counts.
        - Calculates normal video duration via union of GT intervals.
        """
        # Group by video_id
        gt_by_vid: Dict[str, List[Dict[str, Any]]] = {}
        for g in gt_events:
            gt_by_vid.setdefault(g.get("video_id", "default"), []).append(g)

        pred_by_vid: Dict[str, List[Dict[str, Any]]] = {}
        for p in pred_events:
            pred_by_vid.setdefault(p.get("video_id", "default"), []).append(p)

        all_vids = sorted(set(gt_by_vid.keys()).union(set(pred_by_vid.keys())))

        tp = 0
        fp = 0
        fn = 0
        matched_pairs = []
        signed_onset_errors: List[float] = []
        detection_delays: List[float] = []
        early_alert_count = 0

        subgroups = {
            "direction": {
                "LEFT": {"gt": 0, "tp": 0},
                "RIGHT": {"gt": 0, "tp": 0},
                "OTHER": {"gt": 0, "tp": 0}
            },
            "duration": {
                "short_<2s": {"gt": 0, "tp": 0},
                "long_>=2s": {"gt": 0, "tp": 0}
            }
        }

        timeline_rows = []

        for vid in all_vids:
            vid_gts = gt_by_vid.get(vid, [])
            vid_preds = pred_by_vid.get(vid, [])

            # Tally GT subgroups
            for g in vid_gts:
                d = g.get("direction", "OTHER")
                if d in subgroups["direction"]:
                    subgroups["direction"][d]["gt"] += 1
                else:
                    subgroups["direction"]["OTHER"]["gt"] += 1

                dur = g["duration"]
                dur_cat = "short_<2s" if dur < 2.0 else "long_>=2s"
                subgroups["duration"][dur_cat]["gt"] += 1

            # Strict 1-to-1 matching
            # Build all candidate pairs (tiou >= min_tiou) sorted by tIoU descending
            candidate_pairs = []
            for p_idx, p in enumerate(vid_preds):
                p_interval = p["interval"]
                p_target = p.get("target_id_anonymous", "")
                for g_idx, g in enumerate(vid_gts):
                    g_target = g.get("target_id_anonymous", "")
                    if p_target and g_target and p_target != g_target:
                        continue  # target subject mismatch

                    g_interval = g["interval"]
                    tiou = temporal_iou(p_interval, g_interval)
                    if tiou >= self.min_tiou:
                        candidate_pairs.append((tiou, p_idx, g_idx))

            # Greedy 1-to-1 selection by highest tIoU
            candidate_pairs.sort(key=lambda x: x[0], reverse=True)
            matched_pred_indices = set()
            matched_gt_indices = set()

            for tiou, p_idx, g_idx in candidate_pairs:
                if p_idx in matched_pred_indices or g_idx in matched_gt_indices:
                    continue
                matched_pred_indices.add(p_idx)
                matched_gt_indices.add(g_idx)

                p = vid_preds[p_idx]
                g = vid_gts[g_idx]
                tp += 1

                # Signed onset error: pred_start - gt_start
                signed_error = p["interval"][0] - g["interval"][0]
                signed_onset_errors.append(signed_error)
                pos_delay = max(0.0, signed_error)
                detection_delays.append(pos_delay)
                if signed_error < 0:
                    early_alert_count += 1

                matched_pairs.append({
                    "video_id": vid,
                    "gt_event_id": g.get("event_id"),
                    "gt_interval": g["interval"],
                    "pred_interval": p["interval"],
                    "tiou": round(tiou, 4),
                    "signed_onset_error": round(signed_error, 4),
                    "detection_delay": round(pos_delay, 4)
                })

                timeline_rows.append({
                    "video_id": vid,
                    "type": "PREDICTION_TP",
                    "start_s": p["interval"][0],
                    "end_s": p["interval"][1],
                    "matched_gt_id": g.get("event_id"),
                    "tiou": round(tiou, 4)
                })

                d = g.get("direction", "OTHER")
                if d in subgroups["direction"]:
                    subgroups["direction"][d]["tp"] += 1
                else:
                    subgroups["direction"]["OTHER"]["tp"] += 1

                dur = g["duration"]
                dur_cat = "short_<2s" if dur < 2.0 else "long_>=2s"
                subgroups["duration"][dur_cat]["tp"] += 1

            # Unmatched predictions are FP
            for p_idx, p in enumerate(vid_preds):
                if p_idx not in matched_pred_indices:
                    fp += 1
                    timeline_rows.append({
                        "video_id": vid,
                        "type": "PREDICTION_FP",
                        "start_s": p["interval"][0],
                        "end_s": p["interval"][1],
                        "matched_gt_id": None,
                        "tiou": 0.0
                    })

            # Unmatched GT in this video are FN
            for g_idx, g in enumerate(vid_gts):
                if g_idx not in matched_gt_indices:
                    fn += 1
                    timeline_rows.append({
                        "video_id": vid,
                        "type": "GROUND_TRUTH_FN",
                        "start_s": g["interval"][0],
                        "end_s": g["interval"][1],
                        "matched_gt_id": g.get("event_id"),
                        "tiou": 0.0
                    })

        total_gt = len(gt_events)
        total_pred = len(pred_events)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / total_gt if total_gt > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Timing statistics
        stats_signed_error = {}
        stats_detection_delay = {}
        if signed_onset_errors:
            stats_signed_error = {
                "mean": round(float(np.mean(signed_onset_errors)), 4),
                "median": round(float(np.median(signed_onset_errors)), 4),
                "p95": round(float(np.percentile(signed_onset_errors, 95)), 4),
                "min": round(float(np.min(signed_onset_errors)), 4),
                "max": round(float(np.max(signed_onset_errors)), 4)
            }
            stats_detection_delay = {
                "mean": round(float(np.mean(detection_delays)), 4),
                "median": round(float(np.median(detection_delays)), 4),
                "p95": round(float(np.percentile(detection_delays, 95)), 4)
            }

        # Calculate normal video duration
        # If total_normal_duration_minutes is explicitly passed, use it; otherwise compute from video_durations
        normal_duration_sec = 0.0
        calculated_from_union = False
        if total_normal_duration_minutes is not None:
            normal_duration_sec = total_normal_duration_minutes * 60.0
        elif video_durations:
            calculated_from_union = True
            for vid, v_dur in video_durations.items():
                vid_gt_ints = [g["interval"] for g in gt_by_vid.get(vid, [])]
                cheat_dur = compute_union_duration(vid_gt_ints)
                normal_dur = max(0.0, v_dur - cheat_dur)
                normal_duration_sec += normal_dur

        normal_duration_min = normal_duration_sec / 60.0
        if normal_duration_min <= 0.0:
            far_result: Union[str, float] = "not_applicable"
        else:
            far_result = round(fp / normal_duration_min, 4)

        return {
            "evaluation_split": self.split,
            "matching_protocol": "strict_one_to_one_tiou",
            "min_tiou_threshold": self.min_tiou,
            "red_duration_threshold_seconds": self.red_duration_thresh,
            "total_ground_truth_events": total_gt,
            "total_predicted_events": total_pred,
            "normal_duration_seconds": round(normal_duration_sec, 2),
            "normal_duration_minutes": round(normal_duration_min, 4),
            "metrics": {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "event_precision": round(precision, 4),
                "event_recall": round(recall, 4),
                "event_f1_score": round(f1, 4),
                "early_alert_count": early_alert_count,
                "early_alert_rate": round(early_alert_count / tp, 4) if tp > 0 else 0.0,
                "signed_onset_error": stats_signed_error,
                "detection_delay": stats_detection_delay,
                "false_alerts_per_minute_normal": far_result
            },
            "subgroups": subgroups,
            "matched_pairs": matched_pairs,
            "timeline": timeline_rows
        }

    def run(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        out_dir = output_dir or "data/benchmark_reports/posture_eval"
        os.makedirs(out_dir, exist_ok=True)

        gt_events = self.load_ground_truth_events()
        if not gt_events:
            print(f"[WARN] No posture ground-truth events found for split='{self.split}'.")
            empty_summary = {
                "status": "BLOCKED",
                "reason": f"No ground truth events found in split '{self.split}'",
                "split": self.split,
                "manifest": create_version_manifest(
                    dataset_dir=self.dataset_dir,
                    dataset_metadata_path=os.path.join(self.dataset_dir, "annotations", "events.csv"),
                    split=self.split
                )
            }
            summary_path = os.path.join(out_dir, "posture_eval_summary.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(empty_summary, f, indent=2)
            return empty_summary

        sessions = self.load_session_metadata()
        video_durations = {}
        for vid, s_data in sessions.items():
            try:
                video_durations[vid] = float(s_data.get("duration_seconds", 0.0))
            except ValueError:
                pass

        pred_events: List[Dict[str, Any]] = []
        results = self.match_events(gt_events, pred_events, video_durations=video_durations)
        manifest = create_version_manifest(
            dataset_dir=self.dataset_dir,
            dataset_metadata_path=os.path.join(self.dataset_dir, "annotations", "events.csv"),
            split=self.split,
            config={
                "min_tiou": self.min_tiou,
                "onset_tolerance_sec": self.onset_tolerance_sec,
                "red_duration_thresh": self.red_duration_thresh,
                "split": self.split
            }
        )
        results["version_manifest"] = manifest

        summary_path = os.path.join(out_dir, f"posture_eval_{self.split}_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return results


def main():
    parser = argparse.ArgumentParser(description="Reproducible Head-Turning Event Evaluation Harness (Sprint 2.1A)")
    parser.add_argument("--dataset-dir", type=str, default="datasets/posture", help="Path to posture dataset")
    parser.add_argument("--split", type=str, default="test", help="Split to evaluate: test | val | train")
    parser.add_argument("--min-tiou", type=float, default=0.30, help="Minimum temporal IoU for positive match")
    parser.add_argument("--onset-tolerance", type=float, default=0.75, help="Onset time tolerance in seconds")
    parser.add_argument("--red-thresh", type=float, default=1.25, help="Threshold in seconds for RED severity")
    parser.add_argument("--output-dir", type=str, default="data/benchmark_reports/posture_eval", help="Directory to save evaluation reports")
    args = parser.parse_args()

    harness = PostureEventEvaluationHarness(
        dataset_dir=args.dataset_dir,
        split=args.split,
        min_tiou=args.min_tiou,
        onset_tolerance_sec=args.onset_tolerance,
        red_duration_thresh=args.red_thresh
    )
    res = harness.run(output_dir=args.output_dir)
    print("\n--- EVENT-LEVEL METRICS RESULT ---")
    print(json.dumps(res.get("metrics", {}), indent=2))


if __name__ == "__main__":
    main()
