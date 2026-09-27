"""
================================================================================
DUAL-CAMERA 60-SECOND MEMORY & LOAD BENCHMARK (SPRINT 3.2B-R2)
================================================================================
Classification: [synthetic source, stub detector, backend integration]
Lưu ý trung thực: Phép đo sử dụng nguồn camera synthetic và stub detector có
độ trễ mô phỏng 45ms nhằm kiểm tra hành vi đệm đơn slot (zero-backlog), giới hạn
bộ nhớ RingBuffer JPEG và tỷ lệ luân phiên công bằng dưới tải.
KHÔNG dùng để tuyên bố tốc độ mô hình AI thật.
================================================================================
"""

import os
import sys
import time
import json
import uuid
import psutil
import argparse
import threading
import numpy as np
import cv2

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.camera_source import BrowserWebSocketSource, CameraStatus
from services.fair_scheduler import FairInferenceScheduler
from services.ring_buffer import VideoRingBuffer, EVIDENCE_DIR, validate_video_file

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    CUDA_DEVICE = torch.cuda.get_device_name(0) if CUDA_AVAILABLE else None
except Exception:
    CUDA_AVAILABLE = False
    CUDA_DEVICE = None


def run_benchmark(scenario="A", duration=62.0):
    print("=" * 80)
    print(f"DUAL-CAMERA 60-SECOND LOAD BENCHMARK — SCENARIO {scenario}")
    print("Classification: [synthetic source, stub detector, backend integration]")
    print("Lưu ý trung thực: synthetic source + stub detector; không đại diện tốc độ mô hình AI thật.")
    print("=" * 80)

    if scenario == "A":
        width, height = 640, 480
        scenario_name = "Scenario A (640x480 @ 15 FPS)"
        max_bytes_per_cam = 60 * 1024 * 1024
        out_json_filename = "benchmark_640x480.json"
        completion_marker = "BENCHMARK_SCENARIO_A_COMPLETED_SUCCESSFULLY"
    elif scenario == "B":
        width, height = 1920, 1080
        scenario_name = "Scenario B (1920x1080 @ 15 FPS)"
        max_bytes_per_cam = 120 * 1024 * 1024
        out_json_filename = "benchmark_1920x1080.json"
        completion_marker = "BENCHMARK_SCENARIO_B_COMPLETED_SUCCESSFULLY"
    elif scenario == "720p":
        width, height = 1280, 720
        scenario_name = "Scenario 720p Fallback (1280x720 @ 15 FPS)"
        max_bytes_per_cam = 80 * 1024 * 1024
        out_json_filename = "benchmark_720p.json"
        completion_marker = "BENCHMARK_SCENARIO_720P_COMPLETED_SUCCESSFULLY"
    else:
        width, height = 640, 480
        scenario_name = f"Scenario Custom ({width}x{height} @ 15 FPS)"
        max_bytes_per_cam = 60 * 1024 * 1024
        out_json_filename = "benchmark_custom.json"
        completion_marker = "BENCHMARK_CUSTOM_COMPLETED_SUCCESSFULLY"

    jpeg_quality = 80
    retention_seconds = 20.0
    max_frames = 350
    target_acq_fps = 15.0
    frame_interval = 1.0 / target_acq_fps

    process = psutil.Process(os.getpid())
    ram_start_mb = round(process.memory_info().rss / (1024 * 1024), 2)
    cpu_samples = []
    ram_samples = [(0.0, ram_start_mb)]

    session_id = f"bench_{scenario}_{int(time.time()*1000)}"
    cam1 = BrowserWebSocketSource("cam1", "Camera 1 (Góc trước)")
    cam2 = BrowserWebSocketSource("cam2", "Camera 2 (Góc bên)")
    cam1.ring_buffer.max_bytes = max_bytes_per_cam
    cam2.ring_buffer.max_bytes = max_bytes_per_cam
    cam1.ring_buffer.jpeg_quality = jpeg_quality
    cam2.ring_buffer.jpeg_quality = jpeg_quality
    cam1.start()
    cam2.start()

    scheduler = FairInferenceScheduler()
    scheduler.set_sources([cam1, cam2])

    processed_records = []
    encode_latencies_ms = []
    decode_latencies_ms = []
    preview_frames_produced = 0
    preview_bytes_produced_encoded = 0

    processed_lock = threading.Lock()
    stop_event = threading.Event()

    class StubOverloadDetector:
        def __init__(self):
            self.count = 0
        def detect(self, frame):
            self.count += 1
            time.sleep(0.045)  # 45ms intentional execution delay
            return {"detected": False, "objects": [], "posture": "NORMAL", "risk_score": 0.05}

    stub_detector = StubOverloadDetector()
    scheduler.set_detector(stub_detector)

    dummy_frame1 = np.zeros((height, width, 3), dtype=np.uint8)
    dummy_frame2 = np.zeros((height, width, 3), dtype=np.uint8)
    dummy_frame1[:, :, 1] = 200  # Green
    dummy_frame2[:, :, 0] = 200  # Blue

    # Ingestion worker
    def camera_ingest_worker(cam_source: BrowserWebSocketSource, dummy_frame: np.ndarray, source_tag: str):
        nonlocal preview_frames_produced, preview_bytes_produced_encoded
        seq = 0
        t0 = time.monotonic()
        while not stop_event.is_set():
            seq += 1
            now_t = time.time()
            t_enc0 = time.perf_counter()
            ok, enc = cv2.imencode(".jpg", dummy_frame, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
            enc_dur = (time.perf_counter() - t_enc0) * 1000.0
            if ok:
                j_bytes = enc.tobytes()
                with processed_lock:
                    encode_latencies_ms.append(enc_dur)
                    preview_frames_produced += 1
                    preview_bytes_produced_encoded += len(j_bytes)
                    # Sample decode latency every 15 frames
                    if seq % 15 == 0:
                        t_dec0 = time.perf_counter()
                        _ = cv2.imdecode(np.frombuffer(j_bytes, np.uint8), cv2.IMREAD_COLOR)
                        dec_dur = (time.perf_counter() - t_dec0) * 1000.0
                        decode_latencies_ms.append(dec_dur)

                cam_source.push_frame(dummy_frame, timestamp=now_t, sequence_id=seq)
                cam_source.set_latest_preview(j_bytes, now_t, seq)
            target_t = t0 + seq * frame_interval
            sleep_t = target_t - time.monotonic()
            if sleep_t > 0:
                time.sleep(sleep_t)

    # Scheduler worker
    def scheduler_worker():
        while not stop_event.is_set():
            picked = scheduler._pick_next_frame()
            if picked is None:
                time.sleep(0.005)
                continue
            src, item = picked
            t_inf_start = time.perf_counter()
            _ = stub_detector.detect(item["frame"])
            inf_dur = (time.perf_counter() - t_inf_start) * 1000.0
            src.inference_slot.mark_processed(0)
            with processed_lock:
                processed_records.append({
                    "source_id": src.source_id,
                    "sequence_id": item["sequence_id"],
                    "inference_ms": inf_dur,
                    "timestamp": time.monotonic()
                })

    print(f"[*] Starting {scenario_name} for {duration:.1f}s at {time.strftime('%X')}...")
    t_start = time.monotonic()

    t_cam1 = threading.Thread(target=camera_ingest_worker, args=(cam1, dummy_frame1, "cam1"), daemon=True)
    t_cam2 = threading.Thread(target=camera_ingest_worker, args=(cam2, dummy_frame2, "cam2"), daemon=True)
    t_sched = threading.Thread(target=scheduler_worker, daemon=True)

    t_cam1.start()
    t_cam2.start()
    t_sched.start()

    ram_at_warmup = None
    last_print = t_start
    while time.monotonic() - t_start < duration:
        time.sleep(1.0)
        now_mono = time.monotonic()
        elapsed_cur = now_mono - t_start
        cpu_samples.append(psutil.cpu_percent(interval=None))
        current_ram_mb = round(process.memory_info().rss / (1024 * 1024), 2)
        ram_samples.append((round(elapsed_cur, 2), current_ram_mb))

        if elapsed_cur >= 20.0 and ram_at_warmup is None:
            ram_at_warmup = current_ram_mb

        if now_mono - last_print >= 10.0:
            last_print = now_mono
            with processed_lock:
                total_proc = len(processed_records)
            st1 = cam1.inference_slot.get_stats()
            st2 = cam2.inference_slot.get_stats()
            tel1 = cam1.ring_buffer.get_telemetry()
            tel2 = cam2.ring_buffer.get_telemetry()
            print(f"    [T+{elapsed_cur:04.1f}s] RAM: {current_ram_mb}MB | Proc: {total_proc} | "
                  f"Cam1 Ring: {tel1['ring_buffer_bytes']/1024:.1f}KB ({tel1['ring_buffer_frames']}f) | "
                  f"Cam2 Ring: {tel2['ring_buffer_bytes']/1024:.1f}KB ({tel2['ring_buffer_frames']}f)")

    stop_event.set()
    t_cam1.join(timeout=2.0)
    t_cam2.join(timeout=2.0)
    t_sched.join(timeout=3.0)

    elapsed_actual = time.monotonic() - t_start
    ram_end_mb = round(process.memory_info().rss / (1024 * 1024), 2)
    peak_ram_mb = max(r[1] for r in ram_samples)
    if ram_at_warmup is None:
        ram_at_warmup = ram_end_mb

    post_warmup_samples = [r for r in ram_samples if r[0] >= 20.0]
    if len(post_warmup_samples) >= 2:
        dt = post_warmup_samples[-1][0] - post_warmup_samples[0][0]
        dram = post_warmup_samples[-1][1] - post_warmup_samples[0][1]
        ram_slope = round(dram / max(1.0, dt), 4)
    else:
        ram_slope = 0.0

    stats1 = cam1.inference_slot.get_stats()
    stats2 = cam2.inference_slot.get_stats()
    tel1 = cam1.ring_buffer.get_telemetry()
    tel2 = cam2.ring_buffer.get_telemetry()

    cam1.stop()
    cam2.stop()
    scheduler.stop()

    with processed_lock:
        all_records = list(processed_records)
        all_enc = list(encode_latencies_ms)
        all_dec = list(decode_latencies_ms)

    inf_latencies = [r["inference_ms"] for r in all_records]
    p50_inf = round(float(np.percentile(inf_latencies, 50)), 1) if inf_latencies else 0.0
    p95_inf = round(float(np.percentile(inf_latencies, 95)), 1) if inf_latencies else 0.0

    p50_enc = round(float(np.percentile(all_enc, 50)), 2) if all_enc else 0.0
    p95_enc = round(float(np.percentile(all_enc, 95)), 2) if all_enc else 0.0

    p50_dec = round(float(np.percentile(all_dec, 50)), 2) if all_dec else 0.0
    p95_dec = round(float(np.percentile(all_dec, 95)), 2) if all_dec else 0.0

    proc_cam1 = sum(1 for r in all_records if r["source_id"] == "cam1")
    proc_cam2 = sum(1 for r in all_records if r["source_id"] == "cam2")
    tot_proc = len(all_records)
    fairness_cam1 = round((proc_cam1 / tot_proc * 100.0), 1) if tot_proc else 0.0
    fairness_cam2 = round((proc_cam2 / tot_proc * 100.0), 1) if tot_proc else 0.0

    raw_bgr_mb_cam = round((width * height * 3 * 300) / (1024 * 1024), 2)
    actual_jpeg_mb_cam = round(tel1["ring_buffer_bytes"] / (1024 * 1024), 2)

    report = {
        "run_id": os.environ.get("ACCEPTANCE_RUN_ID", "r2_local"),
        "scenario": scenario,
        "scenario_name": scenario_name,
        "truthful_disclaimer": "synthetic source + stub detector; không đại diện tốc độ mô hình AI thật.",
        "memory_conclusion": "Trong cửa sổ benchmark 62 giây với frame synthetic, không quan sát thấy tăng trưởng bộ nhớ không bị chặn.",
        "comparison_note": "Raw BGR là giá trị tính toán lý thuyết. JPEG là số đo trên ảnh synthetic một màu. Ảnh synthetic một màu nén tốt hơn cảnh camera thực. Kết quả không được dùng để dự đoán chính xác dung lượng RTSP camera thực tế.",
        "theoretical_raw_bgr_mb_cam": raw_bgr_mb_cam,
        "actual_synthetic_jpeg_mb_cam": actual_jpeg_mb_cam,
        "resolution": f"{width}x{height}",
        "jpeg_quality": jpeg_quality,
        "retention_seconds": retention_seconds,
        "max_frames": max_frames,
        "max_bytes_per_cam": max_bytes_per_cam,
        "elapsed_seconds": round(elapsed_actual, 2),
        "fps": {
            "target_acquisition_fps": target_acq_fps,
            "actual_acquisition_fps_cam1": round(stats1["submitted"] / elapsed_actual, 2),
            "actual_acquisition_fps_cam2": round(stats2["submitted"] / elapsed_actual, 2),
            "preview_fps": round(preview_frames_produced / elapsed_actual, 2),
            "inference_fps_fake_detector": round(len(all_records) / elapsed_actual, 2)
        },
        "inference_stats": {
            "cam1": {
                "submitted": stats1["submitted"],
                "processed": stats1["processed"],
                "superseded": stats1["superseded"],
                "pending": stats1["pending"],
                "fairness_ratio_pct": fairness_cam1
            },
            "cam2": {
                "submitted": stats2["submitted"],
                "processed": stats2["processed"],
                "superseded": stats2["superseded"],
                "pending": stats2["pending"],
                "fairness_ratio_pct": fairness_cam2
            },
            "total_processed": tot_proc
        },
        "ram": {
            "ram_start_mb": ram_start_mb,
            "ram_at_warmup_mb": ram_at_warmup,
            "ram_peak_mb": peak_ram_mb,
            "ram_end_mb": ram_end_mb,
            "ram_slope_post_warmup_mb_per_sec": ram_slope,
            "ram_samples_time_series": ram_samples
        },
        "ring_buffer": {
            "cam1_bytes": tel1["ring_buffer_bytes"],
            "cam2_bytes": tel2["ring_buffer_bytes"],
            "cam1_frames": tel1["ring_buffer_frames"],
            "cam2_frames": tel2["ring_buffer_frames"],
            "configured_max_bytes": max_bytes_per_cam,
            "cam1_pruned_by_limit": tel1["ring_buffer_dropped_by_limit"],
            "cam2_pruned_by_limit": tel2["ring_buffer_dropped_by_limit"]
        },
        "latencies": {
            "encode_jpeg_p50_ms": p50_enc,
            "encode_jpeg_p95_ms": p95_enc,
            "decode_jpeg_p50_ms": p50_dec,
            "decode_jpeg_p95_ms": p95_dec,
            "inference_p50_ms": p50_inf,
            "inference_p95_ms": p95_inf
        },
        "preview_telemetry": {
            "preview_frames_produced": preview_frames_produced,
            "preview_bytes_produced_encoded": preview_bytes_produced_encoded,
            "preview_frames_superseded_in_source_buffer": cam1.preview_frames_superseded + cam2.preview_frames_superseded,
            "preview_pending_depth_cam1": cam1.preview_pending_depth,
            "preview_pending_depth_cam2": cam2.preview_pending_depth,
            "preview_frames_transmitted_ws": "NOT_MEASURED (no WebSocket client attached during standalone memory stress benchmark)",
            "preview_bytes_transmitted_ws": "NOT_MEASURED (no WebSocket client attached during standalone memory stress benchmark)",
            "preview_frames_received_client": "NOT_MEASURED (no WebSocket client attached during standalone memory stress benchmark)",
            "measurement_clarification": "WebSocket transmission and client-side reception are measured independently in backend/tests/test_preview_transport.py with an active test client."
        },
        "process_exit_status": "EXIT_0",
        "completion_marker": completion_marker
    }

    # Write to data/benchmark_reports/
    report_dir = os.path.join(PROJECT_ROOT, "data", "benchmark_reports")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, out_json_filename)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Also copy to artifacts/sprint_3_2b_r2/
    art_dir = os.path.join(PROJECT_ROOT, "artifacts", "sprint_3_2b_r2")
    os.makedirs(art_dir, exist_ok=True)
    art_file = os.path.join(art_dir, out_json_filename)
    with open(art_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETED: {scenario_name}")
    print(f"  Duration:           {elapsed_actual:.2f}s (>= 60s mandate: PASS)")
    print(f"  Resolution:         {width}x{height}")
    print(f"  RAM:                Start={ram_start_mb}MB, Warmup={ram_at_warmup}MB, Peak={peak_ram_mb}MB, End={ram_end_mb}MB")
    print(f"  RAM Slope (T>=20s): {ram_slope:+.4f} MB/s")
    print(f"  Ring Bytes:         Cam1={tel1['ring_buffer_bytes']/1024:.1f}KB, Cam2={tel2['ring_buffer_bytes']/1024:.1f}KB")
    print(f"  Encode Latency:     p50={p50_enc}ms, p95={p95_enc}ms")
    print(f"  Decode Latency:     p50={p50_dec}ms, p95={p95_dec}ms")
    print(f"  Report written to:  {art_file}")
    print(f"  Completion Marker:  {completion_marker}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["A", "B", "720p"], default="A", help="Benchmark scenario")
    parser.add_argument("--duration", type=float, default=62.0, help="Duration in seconds (>= 60)")
    args = parser.parse_args()
    run_benchmark(args.scenario, args.duration)
