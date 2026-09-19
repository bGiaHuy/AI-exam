# 📚 TÀI LIỆU KỸ THUẬT & KIẾN TRÚC HỆ THỐNG
## DỰ ÁN: AI EXAM CONTROL (GIÁM SÁT THỊ GIÁC & LƯU BẰNG CHỨNG)

---

## 1. PHẠM VI HỆ THỐNG (SYSTEM BOUNDARIES)

Hệ thống được thiết kế theo đúng phạm vi duy nhất:
> **"Hệ thống sử dụng thị giác máy tính để phát hiện hành vi nghi vấn gian lận trong phòng thi, tự động trích xuất video bằng chứng và lưu thông tin sự kiện vào cơ sở dữ liệu."**

### 1.1. Các hành vi giám sát trong phạm vi
- **Phát hiện điện thoại di động (`PHONE`):** Nhận diện thiết bị điện thoại trong khung hình qua mô hình YOLO Phone.
- **Phát hiện tư thế quay đầu / nhìn bài (`HEAD_TURNING`):**
  - Trích xuất 17 điểm khung xương tư thế người bằng mô hình YOLO Pose (`yolo11m-pose.pt`). Bộ lọc EMA ($\alpha = 0.75$) được thiết kế nhằm giảm rung giật (jitter) tọa độ pixel giữa các khung hình liên tiếp; hiệu quả định lượng cần được xác lập trên tập kiểm thử có ground truth.
  - Phân tích góc quay mặt (dựa trên tỷ lệ khoảng cách giữa mũi, mắt trái, mắt phải, tai trái, tai phải).
  - Cảnh báo cờ Vàng (`SUSPICIOUS`): Khi góc quay mặt lệch khỏi bài thi nhưng thời gian duy trì dưới 1.25s.
  - Leo thang cờ Đỏ (`CHEATING_POSTURE`): Khi hành vi quay đầu duy trì liên tục từ 1.25s trở lên.

### 1.2. Cơ chế theo dõi (Tracking)
- Sử dụng thuật toán ByteTrack gán mã định danh tạm thời `track_id` (số nguyên) cho từng người xuất hiện trong luồng video.
- Không nhận dạng danh tính, không liên kết với thông tin cá nhân.

### 1.3. Lưu ý Liêm chính Đánh giá & Chỉ số
- Các chỉ số độ chính xác ghi nhận trong checkpoint `phone_detector_v5.pt` (mAP@0.5 = 76.92%, Precision = 76.22%, Recall = 68.37%) là **training-validation metrics** đo trên tập validation nội bộ khi huấn luyện, không phải là kết quả kiểm định độc lập (independent holdout test metrics).
- Checkpoint `phone_detector_v5.pt` ghi nhận Epoch 60 đạt điểm fitness cao nhất; do không lưu trữ đồng thời hai tệp `best.pt` và `last.pt` riêng biệt nên không khẳng định hai tệp có mã băm (hash) giống nhau.
- Các mục tiêu cải tiến mô hình trong tài liệu được hiểu là **mục tiêu đề xuất (proposed target)**, cần kiểm chứng định lượng qua benchmark có nhãn.

---

## 2. KIẾN TRÚC BACKEND & PIPELINE XỬ LÝ (FASTAPI + SQLITE 3)

### 2.1. Cấu trúc thư mục Backend
```
backend/
├── main.py                     # Khởi chạy FastAPI server, mount static /evidence, CORS
├── database.py                 # Cấu hình kết nối SQLite 3 WAL mode (cheating_system.db)
├── models.py                   # SQLAlchemy ORM Model duy nhất: Incident
├── schemas.py                  # Pydantic schemas cho Incident, Settings, Detection, SessionReset
├── seed_minimal.py             # Script nạp dữ liệu mẫu ban đầu vào bảng incidents
├── migrate_db.py               # Script di trú schema an toàn
├── routers/
│   ├── incidents.py            # API truy vấn, phân trang và xác nhận vi phạm
│   ├── settings.py             # API đọc/lưu cấu hình độ nhạy AI
│   └── ai_engine.py            # API suy luận frame, WebSocket ingest, phát luồng MJPEG, tải clip
├── services/
│   ├── ring_buffer.py          # Circular RingBuffer ghi video clip pre/post-roll (15 FPS target)
│   ├── db_queue.py             # Hàng đợi ghi tuần tự đa luồng an toàn vào SQLite
│   ├── inference_worker.py     # Worker suy luận tách rời với SingleSlotInferenceBuffer
│   └── temporal_tracker.py     # Bộ theo dõi tư thế thời gian thực với Temporal Continuity Guard
└── tests/
    └── test_refactored_system.py # Bộ kiểm thử tự động toàn diện 25 tiêu chí nghiệm thu
```

### 2.2. Tách Rời Hai Pipeline Độc Lập (Sprint 1.2A Architecture)
Để khắc phục hiện tượng nghẽn cổ chai khi client gửi frame với tần suất thấp (~1.67 FPS do chờ suy luận HTTP tuần tự), kiến trúc Sprint 1.2A tách rời hai luồng xử lý:
1. **Pipeline 1 (Evidence Recording):**
   - Tiếp nhận luồng frame nhị phân liên tục qua WebSocket `/api/ws/ingest` với tần suất mục tiêu **15 FPS** (~66ms/frame).
   - Đóng gói header 16 bytes: `sequence_id` (int64, big-endian) và `monotonic_timestamp` (float64, big-endian) cùng dữ liệu ảnh JPEG nhị phân.
   - Toàn bộ frame hợp lệ được đẩy thẳng vào `RingBuffer` ngay khi máy chủ nhận được mà không chờ mô hình AI.
   - RingBuffer giữ 5.0s pre-roll và 10.0s post-roll, xuất container MP4 chuẩn hóa **15.0 FPS**.
2. **Pipeline 2 (AI Inference):**
   - Sử dụng **Single-Slot Queue (dung lượng = 1)** (`SingleSlotInferenceBuffer`).
   - Khối suy luận nền daemon (`InferenceWorker`) chỉ lấy frame mới nhất từ slot đệm.
   - Backlog depth luôn duy trì $\le 1$ tại mọi thời điểm; frame cũ chưa kịp suy luận khi frame mới tới sẽ bị thay thế (superseded) ngay lập tức, không xếp hàng gây trễ tích lũy.
   - Tốc độ suy luận AI (dù phần cứng nhanh hay chậm) không làm chậm tần suất ghi hình bằng chứng của Pipeline 1.

### 2.3. WebSocket Ingestion, Validation, Async Handoff & Session Isolation
- **Endpoint:** `ws://localhost:8000/api/ws/ingest?source_id=...&session_id=...`
- **Validation tham số kết nối:** `source_id` và `session_id` được kiểm tra regex nghiêm ngặt (`^[a-zA-Z0-9_\-\.]{1,64}$`). Nếu vi phạm, WebSocket lập tức đóng với mã 1008 (Policy Violation).
- **Ràng buộc gói nhị phân (Packet Bounds):**
  - Kích thước tối thiểu: 20 bytes (16 bytes header + 4 bytes JPEG tối thiểu). Gói nhỏ hơn bị hủy bỏ.
  - Kích thước tối đa: 3 MB. Gói lớn hơn ngưỡng bị loại bỏ để chống tấn công cạn kiệt bộ nhớ.
  - Header unpack: `sequence_id` (int64 >= 0) và `monotonic_timestamp` (float64 > 0, hữu hạn, không NaN/Inf).
  - Sequence guard: Phát hiện sequence trùng lặp (`seq <= last_seq_id`), out-of-order, hoặc khoảng nhảy (gap) và ghi log cảnh báo.
- **An toàn Async/Thread:** Kết quả suy luận từ worker thread được gửi về event loop của FastAPI thông qua `loop.call_soon_threadsafe`, bảo vệ bởi cờ `is_session_active` và kiểm tra trạng thái WebSocket `CONNECTED` nhằm ngăn chặn rò rỉ pending future khi client ngắt kết nối.
- **Cô lập trạng thái phiên (Session State Isolation):** Khi client ngắt kết nối hoặc gọi `POST /api/session/reset`, toàn bộ trạng thái phiên cũ bao gồm ByteTrack (`BYTETracker.reset()`), TemporalPostureTracker (`reset_session`), SingleSlotInferenceBuffer (`clear_session`), và RingBuffer (pre-roll + tasks) đều được dọn sạch, đảm bảo track ID và bộ đệm bắt đầu lại từ đầu cho phiên mới.
- **Backpressure Control:** Phía frontend kiểm tra `ws.bufferedAmount > 65536` (ngưỡng 64KB), nếu vượt quá sẽ chủ động drop frame từ tầng transport và ghi nhận vào counter `transport_dropped_frames`.
- **Telemetry 4 Counters:** Frontend và backend đồng bộ theo dõi 4 biến đếm: `capture_frames`, `sent_frames`, `transport_dropped_frames`, `received_frames`.

### 2.4. Temporal Continuity Guard (Quy Tắc Liên Tục Thời Gian)
- Khắc phục lỗi leo thang cờ ĐỎ sai lệch khi xảy ra mất frame hoặc đứt quãng mạng:
- Điều kiện kích hoạt cờ ĐỎ quay đầu (`CHEATING_POSTURE`):
  1. Tổng thời lượng nghi vấn liên tục $\Delta t = t_{\text{curr}} - t_{\text{first}} \ge 1.25$ giây.
  2. Khoảng cách thời gian giữa 2 frame nghi vấn liên tiếp liền kề $\le 0.75$ giây (`max_gap_seconds = 0.75`). Nếu vượt quá 0.75s (do mất frame hoặc gián đoạn mạng), hệ thống tự động reset mốc thời gian ban đầu về frame hiện tại.
  3. Tối thiểu $\ge 3$ quan sát nghi vấn (`min_samples = 3`).
- **Kiểm chứng:** Temporal guard đã vượt qua kiểm thử synthetic test: trong kịch bản giả lập đứt quãng mạng giữa hai thời điểm cách nhau $> 0.75$s, hệ thống reset chuỗi quan sát và không leo thang cờ Đỏ sai lệch.

### 2.5. Hàng đợi ghi tuần tự SQLite (DBWriteQueue)
Để ngăn chặn lỗi khóa tài nguyên `sqlite3.OperationalError: database is locked` khi có nhiều luồng nền cùng xuất clip và lưu sự kiện vào SQLite, hệ thống triển khai một worker thread duy nhất tiêu thụ các tác vụ ghi tuần tự từ hàng đợi `queue.Queue`.

---

## 3. CƠ SỞ DỮ LIỆU & QUY CHUẨN LƯU TRỮ

- Tập tin cơ sở dữ liệu: `./cheating_system.db`
- Chế độ: WAL (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) hỗ trợ xử lý truy cập đồng thời (concurrency) hiệu quả hơn giữa các luồng đọc API và luồng ghi sự cố, tránh nghẽn khóa database; không phải là cơ chế bảo mật hay an toàn dữ liệu toàn diện.
- Bảng duy nhất: `incidents`
```sql
CREATE TABLE incidents (
    id VARCHAR(100) NOT NULL PRIMARY KEY,
    source_id VARCHAR(100) NOT NULL,
    track_id INTEGER,
    violation_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    level VARCHAR(20) NOT NULL,
    detected_at DATETIME NOT NULL,
    clip_started_at DATETIME,
    clip_ended_at DATETIME,
    video_path VARCHAR(255),
    snapshot_path VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    proctor_notes TEXT,
    created_at DATETIME NOT NULL
);
```

---

## 4. GIAO DIỆN NGƯỜI DÙNG (REACT 19 FRONTEND)

### 4.1. Các thành phần giao diện
1. **`TopNavBar.tsx`:** Thanh tiêu đề gọn nhẹ, hiển thị nguồn giám sát, đồng hồ thời gian thực và trạng thái AI Engine.
2. **`StreamlinedProctorDashboard.tsx`:**
   - Cột trái (70%): Viewport camera trực tiếp (hỗ trợ Webcam máy trạm hoặc tập tin video kiểm thử), vẽ bounding box vi phạm và HUD đo FPS.
   - Cột phải (30%): Bảng dữ liệu sự cố vi phạm gần nhất, hiển thị ảnh chụp snapshot, nút "Xem clip", "Xác nhận" và "Bỏ qua".
3. **`AISettingsView.tsx`:** Bảng cấu hình trực quan các thông số: ngưỡng tin cậy phát hiện điện thoại, thời gian kích hoạt quay đầu, thời lượng pre-roll, post-roll và thời gian giãn cách cooldown.
4. **`VideoEvidenceModal.tsx`:** Hộp thoại phát lại video bằng chứng MP4 trích xuất từ camera, hỗ trợ xem chậm 0.5x, 1.0x, 1.5x và tải video về máy.

---

## 5. ĐẶC TẢ API ENDPOINTS

| Phương thức | Endpoint | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Kiểm tra trạng thái máy chủ, chế độ lưu trữ |
| `GET` | `/api/incidents` | Lấy danh sách sự cố (hỗ trợ lọc `source_id`, `level`, `status`, `limit`, `skip`) |
| `PATCH` | `/api/incidents/{id}/confirm` | Cập nhật trạng thái sự cố: `confirmed`, `dismissed` hoặc `pending` |
| `GET` | `/api/settings/ai` | Lấy cấu hình độ nhạy AI và RingBuffer hiện tại |
| `POST` | `/api/settings/ai` | Cập nhật cấu hình độ nhạy AI và đồng bộ ngay vào bộ nhớ |
| `POST` | `/api/detect/frame` | Suy luận vi phạm trên 1 khung hình (Base64 JPEG), kích hoạt RingBuffer khi có cờ Đỏ |
| `GET` | `/api/status` | Trạng thái trực tuyến của mô hình AI và CSDL |
| `GET` | `/api/stream` | Luồng video MJPEG thời gian thực có gắn nhãn bounding box |
| `WS` | `/api/ws/ingest` | WebSocket nhị phân nhận luồng frame 15 FPS (recording & inference) |
| `POST` | `/api/session/reset` | Đặt lại trạng thái AI session (ByteTrack, temporal tracker, buffer) |
| `GET` | `/evidence/{filename}` | Tải hoặc phát trực tiếp file video clip bằng chứng MP4 |

