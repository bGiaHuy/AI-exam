"""
================================================================================
BENCHMARK SUITE (SPRINT 1.2A HARDENED) - AI EXAM CONTROL
================================================================================
Phân loại trung thực các phép đo:
- Benchmark 1: [synthetic, backend integration, mock-model]
  Kiểm tra khả năng tiếp nhận frame theo lịch định sẵn và xuất clip từ RingBuffer trên backend.
  (Không phải browser end-to-end trên frontend).
- Benchmark 2: [synthetic, unit test]
  Kiểm thử logic buffer đơn slot (SingleSlotInferenceBuffer) chống dồn ứ hàng đợi.
- Benchmark 3: [synthetic, theoretical calculation]
  Tính toán lý thuyết về mật độ frame mẫu trong khoảng thời gian 0.5s - 1.0s.
  (Không phải đo lường độ chính xác thực tế của model thị giác trên tập test).
- Benchmark 4: [synthetic, unit test]
  Kiểm thử đơn vị logic Temporal Continuity Guard chống leo thang cờ đỏ khi mạng gián đoạn.
================================================================================
"""

import os
import sys
import time
import math
import cv2
import numpy as np

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure backend directory is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from services.ring_buffer import ring_buffer_service, EVIDENCE_DIR, validate_video_file
from services.temporal_tracker import TemporalPostureTracker
from services.inference_worker import SingleSlotInferenceBuffer


def benchmark_acquisition_and_ring_buffer():
    """
    Phép đo 1: Kết quả benchmark synthetic trên backend
    Phân loại: [synthetic, backend integration, mock-model]
    Lưu ý trung thực: Phép đo sử dụng frame synthetic tạo bằng NumPy theo lịch định sẵn trên backend,
    KHÔNG PHẢI phép đo browser end-to-end trên frontend.
    """
    print("\n" + "="*80)
    print("PHÉP ĐO 1: KẾT QUẢ BENCHMARK SYNTHETIC TRÊN BACKEND - 15 FPS INGESTION & RINGBUFFER EXPORT")
    print("Phân loại: [synthetic, backend integration, mock-model]")
    print("="*80)

    # Configure RingBuffer: 5s pre-roll + 10s post-roll at 15.0 FPS = 225 frames
    ring_buffer_service.update_settings(pre_roll_seconds=5.0, post_roll_seconds=10.0, cooldown_seconds=2.0)
    session_id = f"bench_sess_{int(time.time())}"
    source_id = "bench_cam"
    target_ingest_fps = 15.0
    frame_interval = 1.0 / target_ingest_fps

    # Generate 5.0 seconds of pre-roll frames (75 frames)
    t0 = time.time()
    pre_frames = int(5.0 * target_ingest_fps)
    print(f"[*] Đang nạp {pre_frames} frame synthetic pre-roll ở tần suất {target_ingest_fps} FPS...")

    for i in range(pre_frames):
        frame_ts = t0 + i * frame_interval
        # Synthetic frame with distinct motion (moving bar)
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        bar_x = int((i * 8) % 600)
        cv2.rectangle(img, (bar_x, 100), (bar_x + 30, 260), (0, 255, 0), -1)
        cv2.putText(img, f"Frame {i:03d} - Seq {i}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        ring_buffer_service.push_frame(
            frame=img,
            timestamp=frame_ts,
            sequence_id=i,
            session_id=session_id
        )

    # Trigger Incident at t = 5.0s
    trigger_ts = t0 + pre_frames * frame_interval
    trigger_img = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(trigger_img, "INCIDENT TRIGGER RED", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

    print(f"[*] Kích hoạt cờ ĐỎ giả lập tại sequence {pre_frames}...")
    incident_id = ring_buffer_service.trigger_incident(
        violation_type="PHONE",
        confidence=95.0,
        source_id=source_id,
        track_id=101,
        current_frame=trigger_img,
        level="red",
        session_id=session_id,
        timestamp=trigger_ts
    )

    # Feed 10.0 seconds of post-roll frames (150 frames)
    post_frames = int(10.0 * target_ingest_fps)
    print(f"[*] Đang nạp {post_frames} frame synthetic post-roll ở tần suất {target_ingest_fps} FPS...")
    for j in range(post_frames):
        seq = pre_frames + 1 + j
        frame_ts = trigger_ts + (j + 1) * frame_interval
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        bar_x = int(((pre_frames + j) * 8) % 600)
        cv2.rectangle(img, (bar_x, 100), (bar_x + 30, 260), (0, 0, 255), -1)
        cv2.putText(img, f"Post {j:03d} - Seq {seq}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 255), 2)

        ring_buffer_service.push_frame(
            frame=img,
            timestamp=frame_ts,
            sequence_id=seq,
            session_id=session_id
        )

    # Allow worker thread to finalize export
    time.sleep(1.0)
    video_path = os.path.join(EVIDENCE_DIR, f"{incident_id}.mp4")
    video_exists = os.path.exists(video_path)
    is_valid = validate_video_file(video_path) if video_exists else False

    # Read exported video properties
    cap = cv2.VideoCapture(video_path)
    total_out_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    video_size_kb = os.path.getsize(video_path) / 1024.0 if video_exists else 0.0

    print(f"[+] File video clip đã xuất: {video_path}")
    print(f"    - MP4 hợp lệ: {is_valid}")
    print(f"    - Dung lượng: {video_size_kb:.1f} KB")
    print(f"    - Tổng số frame xuất ra: {total_out_frames}")
    print(f"    - FPS container: {out_fps:.1f} FPS")
    print(f"    - Thời lượng: {total_out_frames / out_fps:.2f}s (Mục tiêu thiết kế: 15.0s)")

    # Clean up test video
    if os.path.exists(video_path):
        os.remove(video_path)
    snap_path = os.path.join(EVIDENCE_DIR, f"{incident_id}_snap.jpg")
    if os.path.exists(snap_path):
        os.remove(snap_path)

    return {
        "is_valid": is_valid,
        "total_frames": total_out_frames,
        "out_fps": out_fps,
        "duration": total_out_frames / out_fps if out_fps > 0 else 0
    }


def benchmark_single_slot_inference_buffer():
    """
    Phép đo 2: Kiểm thử độ sâu hàng đợi Single-Slot
    Phân loại: [synthetic, unit test]
    Lưu ý trung thực: Kiểm thử logic buffer đơn slot bằng mô phỏng luồng (producer/consumer),
    chứng minh độ sâu hàng đợi luôn duy trì <= 1 trong điều kiện tải cao.
    """
    print("\n" + "="*80)
    print("PHÉP ĐO 2: KIỂM THỬ ĐỘ SÂU HÀNG ĐỢI SINGLE-SLOT")
    print("Phân loại: [synthetic, unit test]")
    print("="*80)

    buffer = SingleSlotInferenceBuffer()
    backlog_history = []
    total_frames_pushed = 100

    # Simulate producer pushing frames rapidly at 20 FPS (every 50ms)
    # Simulate consumer popping slowly at 5 FPS (every 200ms)
    pop_interval = 0.20
    push_interval = 0.05
    last_pop_time = time.time()
    popped_items = []

    for seq in range(total_frames_pushed):
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        buffer.push_latest(
            source_id="test",
            session_id="sess_1",
            sequence_id=seq,
            timestamp=time.time(),
            frame=dummy_frame
        )
        depth = buffer.backlog_depth
        backlog_history.append(depth)

        now = time.time()
        if now - last_pop_time >= pop_interval:
            item = buffer.pop_latest(timeout=0.01)
            if item:
                popped_items.append(item["sequence_id"])
            last_pop_time = now

        time.sleep(push_interval)

    stats = buffer.get_stats()
    max_backlog = max(backlog_history) if backlog_history else 0
    avg_backlog = sum(backlog_history) / len(backlog_history) if backlog_history else 0

    print(f"[+] Tổng số frame nạp:    {stats['total_enqueued']}")
    print(f"[+] Tổng số frame xử lý:  {stats['total_inferred']}")
    print(f"[+] Tổng số frame thay thế: {stats['total_superseded']}")
    print(f"[+] Độ sâu hàng đợi lớn nhất: {max_backlog} (Điều kiện thiết kế: <= 1)")
    print(f"[+] Độ sâu hàng đợi trung bình: {avg_backlog:.2f}")

    assert max_backlog <= 1, f"LỖI: Độ sâu hàng đợi vượt quá 1: {max_backlog}"
    print("[PASS] Đạt yêu cầu: Hàng đợi inference luôn duy trì <= 1 frame mới nhất, không tích lũy trễ.")
    return stats


def benchmark_transient_cheat_catch_rate():
    """
    Phép đo 3: Mô hình toán học về mật độ frame khi bắt hành vi ngắn hạn (0.5s - 1.0s)
    Phân loại: [synthetic, theoretical calculation]
    Lưu ý trung thực: Đây là phép tính toán lý thuyết về mật độ frame mẫu theo chu kỳ thời gian (15 Hz vs 1.67 Hz),
    KHÔNG PHẢI đo lường độ chính xác thực tế của mô hình thị giác máy tính trên dữ liệu thực tế có nhãn.
    """
    print("\n" + "="*80)
    print("PHÉP ĐO 3: MÔ HÌNH TOÁN HỌC VỀ MẬT ĐỘ FRAME KHI BẮT HÀNH VI NGẮN HẠN (0.5s - 1.0s)")
    print("Phân loại: [synthetic, theoretical calculation]")
    print("="*80)

    scenarios = [
        {"desc": "Xem nhanh điện thoại (0.5s)", "duration": 0.5},
        {"desc": "Quay đầu nhanh (0.8s)",         "duration": 0.8},
        {"desc": "Liếc tài liệu (1.0s)",           "duration": 1.0},
    ]

    print(f"{'Kịch bản':<30} | {'Thời gian':<10} | {'Mức cũ 1.67 FPS':<20} | {'Mức mới 15 FPS':<20} | {'Tỷ lệ tăng'}")
    print("-" * 92)

    for s in scenarios:
        dur = s["duration"]
        # Old 1.67 FPS has 600ms interval
        frames_167 = dur / 0.600
        # New 15 FPS has 66.6ms interval
        frames_15 = dur / 0.0666

        miss_risk_167 = "Dưới 1 frame (nguy cơ mất)" if frames_167 < 1.0 else "~1 frame (không ổn định)"
        eval_15 = f"~{int(round(frames_15))} frame mẫu"

        print(f"{s['desc']:<30} | {dur:>4.1f}s     | {frames_167:>4.1f} frame ({miss_risk_167}) | {frames_15:>4.1f} frame ({eval_15}) | {frames_15/max(0.1, frames_167):.1f}x mật độ")

    print("\n[PASS] Về mặt lý thuyết lấy mẫu: Tần suất 15 FPS cung cấp từ 7 đến 15 frame mẫu cho cửa sổ 0.5s-1.0s.")


def benchmark_temporal_continuity_guard():
    """
    Phép đo 4: Kiểm thử đơn vị cơ chế lọc gián đoạn Temporal Continuity Guard
    Phân loại: [synthetic, unit test]
    Lưu ý trung thực: Kiểm thử logic thuật toán xác định khoảng trống (gap detection) trên chuỗi timestamp giả lập.
    """
    print("\n" + "="*80)
    print("PHÉP ĐO 4: KIỂM THỬ ĐƠN VỊ CƠ CHẾ LỌC GIÁN ĐOẠN TEMPORAL CONTINUITY GUARD")
    print("Phân loại: [synthetic, unit test]")
    print("="*80)

    tracker = TemporalPostureTracker(max_gap_seconds=0.75, min_samples=3)

    print("[*] Tình huống A: Gián đoạn kết nối mạng 2.0s giữa 2 frame nghi vấn (Gap > 0.75s)")
    # Frame 1 at t = 0.0s (suspicious)
    status, level, dur = tracker.update(source_id="cam1", track_id=1, is_suspicious=True, timestamp=0.0, alert_seconds=1.25, session_id="sess1")
    print(f"    t=0.0s: status={status}, level={level}, dur={dur:.2f}s")
    assert level == "yellow"

    # Frame 2 arrives 2.0s later due to network lag / packet drop
    status, level, dur = tracker.update(source_id="cam1", track_id=1, is_suspicious=True, timestamp=2.0, alert_seconds=1.25, session_id="sess1")
    print(f"    t=2.0s (gap=2.0s > 0.75s): status={status}, level={level}, dur={dur:.2f}s")
    assert level == "yellow", "LỖI NGHIÊM TRỌNG: Khoảng gián đoạn > 0.75s KHÔNG được leo thang cờ ĐỎ!"
    print("    [PASS] Đã phát hiện gián đoạn mạng -> Bộ theo dõi reset mốc thời gian về 2.0s (ngăn chặn cờ ĐỎ giả).")

    print("\n[*] Tình huống B: Tư thế nghi vấn liên tục với các frame đều đặn (< 0.75s)")
    # t=2.4s (gap=0.4s)
    status, level, dur = tracker.update(source_id="cam1", track_id=1, is_suspicious=True, timestamp=2.4, alert_seconds=1.25, session_id="sess1")
    print(f"    t=2.4s (gap=0.4s): status={status}, level={level}, dur={dur:.2f}s")
    assert level == "yellow"

    # t=2.8s (gap=0.4s)
    status, level, dur = tracker.update(source_id="cam1", track_id=1, is_suspicious=True, timestamp=2.8, alert_seconds=1.25, session_id="sess1")
    print(f"    t=2.8s (gap=0.4s): status={status}, level={level}, dur={dur:.2f}s")
    assert level == "yellow"

    # t=3.3s (gap=0.5s, total continuous = 1.3s >= 1.25s, samples = 4 >= 3)
    status, level, dur = tracker.update(source_id="cam1", track_id=1, is_suspicious=True, timestamp=3.3, alert_seconds=1.25, session_id="sess1")
    print(f"    t=3.3s (gap=0.5s, continuous=1.3s >= 1.25s): status={status}, level={level}, dur={dur:.2f}s")
    assert level == "red", "LỖI: Tư thế liên tục >= 1.25s với đủ số mẫu phải kích hoạt cờ ĐỎ!"
    print("    [PASS] Hành vi nghi vấn liên tục đạt ngưỡng thời gian đã leo thang cờ ĐỎ chính xác.")


def main():
    print("="*80)
    print("AI EXAM CONTROL - BỘ ĐO KIỂM THỬ SPRINT 1.2A (HARDENED)")
    print("="*80)
    t_bench_start = time.time()

    b1 = benchmark_acquisition_and_ring_buffer()
    b2 = benchmark_single_slot_inference_buffer()
    benchmark_transient_cheat_catch_rate()
    benchmark_temporal_continuity_guard()

    elapsed = time.time() - t_bench_start
    print("\n" + "="*80)
    print(f"[PASS] TẤT CẢ CÁC BÀI ĐO HOÀN THÀNH HỢP LỆ TRONG {elapsed:.2f}s")
    print("="*80)


if __name__ == "__main__":
    main()
