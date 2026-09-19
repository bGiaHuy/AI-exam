# 🎓 AI-Powered Automated Proctoring System (AI Exam Control)
### Hệ thống giám sát phòng thi tự động bằng thị giác máy tính & trích xuất video bằng chứng

> **Phạm vi duy nhất:**  
> Hệ thống sử dụng thị giác máy tính để phát hiện hành vi nghi vấn gian lận trong phòng thi, tự động trích xuất video bằng chứng và lưu thông tin sự kiện vào cơ sở dữ liệu.

---

## 📌 1. TỔNG QUAN PHẠM VI (SYSTEM SCOPE)

Hệ thống tập trung 100% vào nghiệp vụ thị giác máy tính và lưu trữ bằng chứng khách quan, hoạt động hoàn toàn **Offline On-Premise** trên máy trạm của giám thị:

### ✅ Chức năng hoạt động:
1. **Nhận video đầu vào:** Hỗ trợ trực tiếp từ Webcam máy trạm hoặc tập tin video clip kiểm thử.
2. **Phát hiện điện thoại (`PHONE`):** Mô hình YOLO phát hiện điện thoại di động trong khu vực làm bài.
3. **Phát hiện quay đầu / tư thế nghi vấn (`HEAD_TURNING`):** Sử dụng YOLO Pose ước lượng 17 điểm khung xương (mũi, mắt, tai, vai) và heuristic góc quay mặt:
   - Cảnh báo cờ Vàng (`SUSPICIOUS`): Khi phát hiện quay đầu góc lớn nhưng chưa đủ thời gian leo thang.
   - Cảnh báo cờ Đỏ (`CHEATING_POSTURE`): Khi hành vi quay đầu duy trì liên tục $\ge 1.25$ giây.
4. **Theo dõi người bằng ByteTrack (`track_id`):** Gán mã số định danh tạm thời (ví dụ: `Track 1`, `Track 2`) thuần túy phục vụ thuật toán theo dõi chuyển động qua các frame; **không định danh danh tính**.
5. **Bộ đệm RingBuffer & Tự động tạo clip bằng chứng:** Tự động cắt clip video bằng chứng khi có cờ ĐỎ với pre-roll (5.0s trước thời điểm vi phạm) và post-roll (10.0s sau thời điểm vi phạm), tổng thời lượng clip ~15.0s. Cờ VÀNG chỉ hiển thị cảnh báo trực tiếp trên HUD mà không kích hoạt tạo clip. Hệ thống nội suy resampling đảm bảo tốc độ phát video đúng chuẩn thời gian thực 1.0x (không bị tua nhanh timelapse do tần suất gửi frame thấp), kiểm tra tính toàn vẹn tập tin bằng OpenCV trước khi lưu trữ.
6. **Lưu trữ siêu dữ liệu vào SQLite (`cheating_system.db`):** Lưu trữ đường dẫn video clip, ảnh chụp snapshot, độ tin cậy và mốc thời gian vi phạm vào bảng duy nhất `incidents` qua hàng đợi tuần tự luồng an toàn (Sequential Thread-safe Write Queue).
7. **Bảng điều khiển giám thị trực quan:** Hiển thị luồng video gắn bounding box thời gian thực, danh sách sự cố gần nhất và modal phát lại video bằng chứng MP4.
8. **Thao tác vận hành viên:** Cho phép giám thị kiểm tra video bằng chứng, chọn "Xác nhận vi phạm" (`confirmed`) hoặc "Bỏ qua" (`dismissed`).
9. **Đồng bộ cấu hình AI:** Cho phép điều chỉnh độ nhạy AI (`phone_confidence`, `posture_alert_seconds`, `suspicion_threshold`, tham số RingBuffer) trực tiếp trên giao diện và lưu bền vững vào `data/ai_settings.json`.

### ❌ Giới hạn phạm vi (Strict Non-Goals):
- **Không có nhận dạng danh tính:** Không lưu tên, SBD, CCCD, ảnh hồ sơ hoặc điểm liêm chính thí sinh.
- **Không có biểu mẫu báo cáo pháp quy:** Không sử dụng mẫu A1/A2/B1, không có chữ ký số canvas.
- **Không có trợ lý AI ngôn ngữ / RAG:** Không sử dụng LangChain, FAISS hay Gemini API.
- **Không phát hiện các hành vi ngoài phạm vi:** Không có rời chỗ ngồi, phao giấy hay phát hiện âm thanh.

---

## 🧱 2. KIẾN TRÚC HỆ THỐNG (ARCHITECTURE)

```
                    ┌────────────────────────────────────────┐
                    │      VIDEO INPUT (Webcam / File)       │
                    └───────────────────┬────────────────────┘
                                        │ (Video Frames)
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND (PORT 8000)                               │
│                                                                                        │
│   ┌────────────────────────┐      ┌────────────────────────┐                           │
│   │ YOLO11m Pose Estimator │      │  YOLO Phone Detector   │                           │
│   │ (17 Keypoints Heuristic)│     │  (phone_detector_v5.pt)│                           │
│   └───────────┬────────────┘      └───────────┬────────────┘                           │
│               └───────────────────┬───────────┘                                        │
│                                   ▼                                                    │
│               ┌─────────────────────────────────────────┐                              │
│               │     ByteTrack Tracker (Anonymous ID)    │                              │
│               └───────────────────┬─────────────────────┘                              │
│                                   │                                                    │
│               ┌───────────────────┴─────────────────────┐                              │
│               ▼                                         ▼                              │
│    ┌──────────────────────┐                 ┌───────────────────────┐                  │
│    │ Time-Based RingBuffer│                 │   DBWriteQueue        │                  │
│    │  (Pre/Post Roll MP4) │                 │(Sequential Thread-Safe│                  │
│    └──────────┬───────────┘                 └──────────┬────────────┘                  │
│               ▼                                        ▼                               │
│    ┌──────────────────────┐                 ┌───────────────────────┐                  │
│    │  ./data/evidence/    │                 │   SQLite 3 (WAL)      │                  │
│    │  (Clips & Snapshots) │                 │ (cheating_system.db)  │                  │
│    └──────────────────────┘                 └───────────────────────┘                  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ REST API / HTTP Static
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             REACT 19 FRONTEND (PORT 3000)                              │
│                                                                                        │
│   ┌──────────────────────────────────┐      ┌──────────────────────────────────────┐   │
│   │  Streamlined Proctor Dashboard   │      │    Video Evidence Playback Modal     │   │
│   │  (Live HUD & Incident Matrix)    │      │    (MP4 Playback & Confirm/Dismiss)  │   │
│   ├──────────────────────────────────┤      └──────────────────────────────────────┘   │
│   │       AI Sensitivity Settings    │                                                 │
│   └──────────────────────────────────┘                                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 3. CƠ SỞ DỮ LIỆU & SCHEMA (SQLITE 3 WAL)

Tập tin cơ sở dữ liệu: `./cheating_system.db`  
Chế độ: `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`

### Bảng duy nhất: `incidents`
| Tên cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | `VARCHAR(100)` | Khóa chính sự cố (`inc_{timestamp}_{uuid}`) |
| `source_id` | `VARCHAR(100)` | Định danh nguồn video (`webcam_local`, `demo_video`) |
| `track_id` | `INTEGER` | Mã số bám vết tạm thời của người vi phạm |
| `violation_type` | `VARCHAR(50)` | Loại vi phạm: `PHONE` hoặc `HEAD_TURNING` |
| `confidence` | `FLOAT` | Độ tin cậy nhận diện (%) |
| `level` | `VARCHAR(20)` | Cấp độ cảnh báo: `red` |
| `detected_at` | `DATETIME` | Mốc thời gian phát hiện (ISO 8601 UTC) |
| `clip_started_at` | `DATETIME` | Mốc thời gian bắt đầu clip bằng chứng |
| `clip_ended_at` | `DATETIME` | Mốc thời gian kết thúc clip bằng chứng |
| `video_path` | `VARCHAR(255)` | Đường dẫn tương đối file clip (`/evidence/{id}.mp4`) |
| `snapshot_path` | `VARCHAR(255)` | Đường dẫn file ảnh snapshot đỉnh điểm vi phạm |
| `status` | `VARCHAR(20)` | Trạng thái: `pending`, `confirmed`, `dismissed` |
| `proctor_notes` | `TEXT` | Ghi chú của giám thị hoặc mô tả chi tiết |
| `created_at` | `DATETIME` | Thời gian bản ghi được tạo |

---

## 🚀 4. HƯỚNG DẪN CÀI ĐẶT & CHẠY HỆ THỐNG

### 4.1. Khởi chạy Backend (FastAPI)
```bash
# Tạo và kích hoạt môi trường ảo biệt lập
uv venv .venv
.venv\Scripts\activate

# Cài đặt phụ thuộc chuẩn hóa
uv pip install -r backend/requirements.txt

# Khởi chạy server API (cổng 8000)
python backend/main.py
```
Backend API sẽ hoạt động tại: `http://localhost:8000`  
Tài liệu Swagger UI: `http://localhost:8000/docs`

### 4.2. Chạy Kiểm Thử Tự Động & Benchmark Định Lượng (Sprint 1.2A Hardened)
```bash
# 1. Chạy toàn bộ 25 tiêu chí nghiệm thu tự động
.venv\Scripts\python.exe -m unittest -v backend/tests/test_refactored_system.py

# 2. Chạy bộ benchmark định lượng synthetic trên backend
.venv\Scripts\python.exe backend/benchmark_pipelines.py
```

Bộ kiểm thử tự động kiểm tra độc lập toàn bộ **25 tiêu chí nghiệm thu**:
1. `test_01_schema_contains_zero_identity`: DB SQLite chỉ chứa bảng `incidents`, không có bảng hoặc cột định danh.
2. `test_02_migration_safe_and_idempotent`: Script `migrate_db.py` an toàn, có backup và idempotent.
3. `test_03_create_phone_violation`: Vi phạm điện thoại cờ ĐỎ ghi nhận chính xác vào SQLite.
4. `test_04_create_head_turning_violation`: Vi phạm quay đầu cờ ĐỎ ghi nhận chính xác vào SQLite.
5. `test_05_yellow_flag_does_not_create_clip_or_db_event`: Cờ VÀNG chỉ hiển thị trực tiếp trên HUD, không tạo clip và không ghi DB.
6. `test_06_red_flag_creates_clip`: Cờ ĐỎ kích hoạt trích xuất clip MP4 vào `./data/evidence/` và lưu DB.
7. `test_07_cooldown_isolates_separate_tracks`: Cooldown cách ly độc lập theo từng track ID.
8. `test_08_cooldown_blocks_duplicate_triggers_on_same_track`: Chặn duplicate triggers trên cùng track ID.
9. `test_09_temporal_rule_uses_real_elapsed_time`: Leo thang quay đầu dựa trên thời gian thực ($\Delta t \ge 1.25$s).
10. `test_10_preroll_5s_and_postroll_10s_duration`: Cấu hình 5.0s pre-roll + 10.0s post-roll (~15.0s tổng thời lượng).
11. `test_11_corrupted_clip_not_saved_as_completed_evidence`: Từ chối lưu video hỏng hoặc 0-byte vào DB.
12. `test_12_db_write_queue_handles_multiple_concurrent_requests_without_dropping`: Xử lý ghi đồng thời không khóa DB.
13. `test_13_settings_affect_runtime_behavior`: Cập nhật cấu hình runtime tức thì qua API.
14. `test_14_api_returns_correct_schema`: Schema phản hồi chuẩn Pydantic và đầy đủ 3 trường FPS.
15. `test_15_frontend_does_not_call_legacy_endpoints`: Quét `src/` chứng minh zero legacy API calls.
16. `test_16_model_weights_loadable`: Nạp thành công weights thật và chạy warm-up inference.
17. `test_17_pipeline_end_to_end_with_fixture`: Toàn trình nạp frame -> kích hoạt cờ ĐỎ -> xuất clip MP4 -> lưu CSDL.
18. `test_18_temporal_continuity_guard`: Mất frame / gap > 0.75s reset bộ đếm, chặn cờ ĐỎ giả mạo; liên tục $\ge 1.25$s leo thang cờ ĐỎ.
19. `test_19_single_slot_inference_buffer_zero_backlog`: Hàng đợi suy luận dung lượng = 1, backlog luôn $\le 1$, frame cũ bị supersede ngay lập tức, AI chậm không cản trở recording.
20. `test_20_ring_buffer_15fps_and_session_isolation`: RingBuffer xuất chuẩn 15 FPS, cô lập pre-roll giữa các phiên tránh trộn clip cũ.
21. `test_21_websocket_binary_ingest_endpoint`: Endpoint WebSocket binary `/api/ws/ingest` tiếp nhận header 16 bytes + JPEG và phân phối sang 2 pipeline.
22. `test_22_websocket_malformed_packets`: Kiểm tra an toàn packet nhị phân (<20B, >3MB, seq_id âm, timestamp bất thường, seq trùng/lùi).
23. `test_23_websocket_query_parameter_validation`: Kiểm tra regex cho `source_id` và `session_id`, từ chối ký tự độc hại với mã 1008.
24. `test_24_websocket_stress_disconnect_during_inference`: Bơm frame dồn dập rồi ngắt kết nối đột ngột, bảo vệ an toàn luồng và async loop.
25. `test_25_session_isolation_and_reset_api`: Endpoint `POST /api/session/reset` làm sạch toàn diện trạng thái ByteTrack, temporal tracker và bộ đệm giữa các phiên.

