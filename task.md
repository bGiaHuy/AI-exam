# 📋 TIẾN ĐỘ THỰC HIỆN REFACTOR DỰ ÁN AI EXAM CONTROL (SPRINT 1.1)
> **Phạm vi duy nhất:**  
> "Hệ thống sử dụng thị giác máy tính để phát hiện hành vi nghi vấn gian lận trong phòng thi, tự động trích xuất video bằng chứng và lưu thông tin sự kiện vào cơ sở dữ liệu."

---

## 🎯 DANH MỤC CÁC HẠNG MỤC ĐÃ HOÀN THÀNH (COMPLETED)

### 1. Đồng bộ Thời Lượng Bằng Chứng & Quy Tắc Cờ
- [x] Cấu hình chính thức: `pre_roll_seconds = 5.0`, `post_roll_seconds = 10.0`, tổng thời lượng clip ~15.0 giây.
- [x] Loại bỏ hoàn toàn cấu hình 5+5 cũ khỏi: `ring_buffer.py`, `settings.py`, `schemas.py`, `evidence.yaml`, `ai_settings.json`, `App.tsx`, `AISettingsView.tsx`, `api.ts`.
- [x] Ràng buộc chặt chẽ: Chỉ cờ ĐỎ (`CHEATING_POSTURE`, `PHONE`) mới kích hoạt tạo clip RingBuffer và lưu CSDL; cờ VÀNG (`SUSPICIOUS`) chỉ hiển thị cảnh báo trực tiếp trên HUD.

### 2. Chuỗi FPS & Temporal Decision
- [x] Đo đạc thời gian thực: Tính khoảng cách $\Delta t$ giữa 2 frame liên tiếp và xuất `observed_acquisition_fps = 1.0 / \Delta t`.
- [x] Phân biệt rõ ràng 3 chỉ số FPS: `observed_acquisition_fps` (tần suất nhận từ client, ~1.67 FPS), `inference_fps` (tốc độ chạy mô hình), `output_video_fps` (tốc độ container 20.0 FPS).
- [x] Quyết định thời gian thực: Theo dõi theo `(source_id, track_id)`, kích hoạt cờ ĐỎ khi $t_{\text{current}} - t_{\text{first\_suspicious}} \ge \text{posture\_alert\_seconds}$ (1.25s), độc lập với tần suất gửi frame của client.
- [x] Resampling tốc độ thực: Nội suy theo lưới thời gian thực và nearest-neighbor matching, đảm bảo clip MP4 phát lại đúng tốc độ tự nhiên 1.0x (không bị lỗi tua nhanh timelapse).

### 3. Đồng Bộ Cài Đặt Runtime (Settings Sync)
- [x] Truy vết và liên kết đầy đủ 6 tham số: `phone_confidence`, `posture_alert_seconds`, `suspicion_threshold`, `pre_roll_seconds`, `post_roll_seconds`, `cooldown_seconds`.
- [x] Áp dụng tức thì: Khi gọi `POST /api/settings/ai`, cập nhật đồng thời file `ai_settings.json`, runtime `detector`, và `ring_buffer_service` mà không cần khởi động lại server.

### 4. Môi Trường Biệt Lập & Nạp Model Thật
- [x] Khởi tạo môi trường ảo độc lập `.venv` bằng `uv venv .venv`.
- [x] Cài đặt 52 thư viện phụ thuộc (`torch==2.14.0`, `ultralytics==8.4.150`, `fastapi`, `sqlalchemy`, `opencv-python`, v.v.) và chuẩn hóa `backend/requirements.txt`.
- [x] Nạp thành công 100% trọng số thật: `model/weights/yolo11m-pose.pt` (42.4 MB) và `model/weights/phone_detector_v5.pt` (19.2 MB).
- [x] Tuân thủ nghiêm ngặt Rule 12: Giữ nguyên vẹn 100% thư mục `model/`.

### 5. Kiểm Tra Tình Trạng Frontend
- [x] Quét hệ thống: Không có `node.exe` trên máy trạm -> Ghi nhận trung thực trạng thái `BLOCKED — chưa kiểm chứng frontend build` theo đúng quy định.
- [x] Rà soát tĩnh toàn bộ mã nguồn `src/`: 100% lời gọi API khớp với router backend hiện tại, zero endpoint cũ.

### 6. Dọn Dẹp Codebase & Phân Loại File
- [x] Gắn nhãn `[LEGACY ARCHIVED GUIDE]` ở đầu `HUONG_DAN_VIET_BAO_CAO_KHKT.md`.
- [x] Phân loại 5 nhóm rõ ràng cho toàn bộ các file còn lại trong dự án.

### 7. Di Trú Cơ Sở Dữ Liệu An Toàn (Database Hardening)
- [x] Tự động tạo backup với timestamp + UUID và kiểm tra tính toàn vẹn (kích thước, `PRAGMA quick_check`).
- [x] Thực thi transaction an toàn (`BEGIN IMMEDIATE TRANSACTION`, `COMMIT`, `ROLLBACK`), tránh lỗi implicit commit của SQLite.
- [x] Đảm bảo tính idempotent: Không làm biến đổi dữ liệu khi chạy lại nhiều lần.
- [x] Bảo vệ `backend/seed_minimal.py` bằng cờ `--dev-only`.

### 8. Bộ Kiểm Thử Tự Động 17 Tiêu Chí Nghiệm Thu (100% PASS)
- [x] `backend/tests/test_refactored_system.py` chạy qua `.venv`: 17/17 tests ĐẠT (OK):
  1. `test_01_schema_contains_zero_identity`: PASS
  2. `test_02_migration_safe_and_idempotent`: PASS
  3. `test_03_create_phone_violation`: PASS
  4. `test_04_create_head_turning_violation`: PASS
  5. `test_05_yellow_flag_does_not_create_clip_or_db_event`: PASS
  6. `test_06_red_flag_creates_clip`: PASS
  7. `test_07_cooldown_isolates_separate_tracks`: PASS
  8. `test_08_cooldown_blocks_duplicate_triggers_on_same_track`: PASS
  9. `test_09_temporal_rule_uses_real_elapsed_time`: PASS
  10. `test_10_preroll_5s_and_postroll_10s_duration`: PASS
  11. `test_11_corrupted_clip_not_saved_as_completed_evidence`: PASS
  12. `test_12_db_write_queue_handles_multiple_concurrent_requests_without_dropping`: PASS
  13. `test_13_settings_affect_runtime_behavior`: PASS
  14. `test_14_api_returns_correct_schema`: PASS
  15. `test_15_frontend_does_not_call_legacy_endpoints`: PASS
  16. `test_16_model_weights_loadable`: PASS
  17. `test_17_pipeline_end_to_end_with_fixture`: PASS
