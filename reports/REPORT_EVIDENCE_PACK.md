# 📊 BỘ BẰNG CHỨNG KỸ THUẬT BÁO CÁO (REPORT EVIDENCE PACK)
## DỰ ÁN: AI-POWERED AUTOMATED PROCTORING SYSTEM (AI EXAM CONTROL)
**Mã văn bản:** `EVID-PACK-V3.0`  
**Ngày lập:** 14/09/2026  
**Cơ sở kiểm chứng:** Toàn bộ mã nguồn thực tế, lược đồ cơ sở dữ liệu SQLite, trọng số mô hình và nhật ký kiểm thử tự động tại commit `8e4a855d582911f03074e9f5f0838276bd9da287` (nhánh `frontandbackend`).  

---

## 1. KIẾN TRÚC HỆ THỐNG ĐÃ ĐƯỢC XÁC MINH TRỰC TIẾP TỪ MÃ NGUỒN

### 1.1. Mô hình Vận hành Tổng thể (System Topology)
Hệ thống vận hành theo kiến trúc **Offline On-Premise**, thực thi cục bộ trên máy trạm của giám thị trong phạm vi đã kiểm thử, không phụ thuộc kết nối Internet, không gọi bất kỳ Cloud API hay CDN bên ngoài nào.

- **Máy chủ Backend:** FastAPI (Python 3.12, Uvicorn) lắng nghe tại cổng `http://127.0.0.1:8000` (hoặc `http://localhost:8000`).
- **Giao diện Giám thị Frontend:** React 19 + TypeScript + Vite + Tailwind CSS phục vụ tại cổng `http://localhost:3000`.
- **Cơ sở dữ liệu:** SQLite 3 với chế độ ghi trước nhật ký (Write-Ahead Logging - WAL mode) lưu tại tập tin `./cheating_system.db`.
- **Kho lưu trữ bằng chứng ngoại tuyến:** Thư mục cục bộ `./data/evidence/` được mount trực tiếp thành static path tại `/evidence`.

### 1.2. Sơ đồ Khối Kiến trúc Phần mềm
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                CLIENT WORKSTATION BROWSER                              │
│                               (React 19 + TypeScript, Port 3000)                       │
│                                                                                        │
│  ┌──────────────────────────────┐        ┌──────────────────────────────────────────┐  │
│  │ StreamlinedProctorDashboard  │        │       VideoEvidenceModal                 │  │
│  │ - Video Capture (Canvas API) │        │       - HTML5 Video Player (/evidence)   │  │
│  │ - Real-time Live HUD Bounding│        │       - Confirm / Dismiss Buttons        │  │
│  │ - Active Session Incident List│       │       - Proctor Notes Input Area         │  │
│  └──────────────┬───────────────┘        └────────────────────┬─────────────────────┘  │
│                 │ (16-byte binary header + JPEG)              │ (PATCH /confirm)       │
└─────────────────┼─────────────────────────────────────────────┼────────────────────────┘
                  │                                             │
      WebSocket /api/ws/ingest (15 FPS)             REST API /api/incidents
                  │                                             │
┌─────────────────▼─────────────────────────────────────────────▼────────────────────────┐
│                              FASTAPI BACKEND ENGINE (Port 8000)                        │
│                                                                                        │
│ ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ WebSocket Connection Manager & Header Unpacker (ai_engine.py)                      │ │
│ │ - Session Isolation Guard & Regex Validator (source_id, session_id)               │ │
│ └─────────────────────────┬──────────────────────────────────────────┬───────────────┘ │
│                           │                                          │                 │
│         [Pipeline 1: Evidence Ingest]              [Pipeline 2: AI Inference]          │
│                           │                                          │                 │
│ ┌─────────────────────────▼───────────┐  ┌───────────────────────────▼───────────────┐ │
│ │ VideoRingBuffer (ring_buffer.py)    │  │ SingleSlotInferenceBuffer (Queue size = 1)│ │
│ │ - Circular Deque (pre 5s / post 10s)│  │ - Worker Daemon (InferenceWorker)          │ │
│ │ - Time-grid Resampling (1.0x speed) │  │ - Backlog depth <= 1 (supersedes stale)   │ │
│ │ - OpenCV File Verification          │  └───────────────────────────┬───────────────┘ │
│ └─────────────────────────┬───────────┘                              │                 │
│                           │                                          │                 │
│                           │       ┌──────────────────────────────────▼───────────────┐ │
│                           │       │ ExamBehaviorDetector (exam_analyzer.py)          │ │
│                           │       │ - YOLO11m Pose (17 Keypoints, ByteTrack)         │ │
│                           │       │ - YOLO Phone Detector (phone_detector_v5.pt)     │ │
│                           │       │ - Keypoint EMA Smoother (alpha = 0.75)           │ │
│                           │       │ - TemporalPostureTracker (alert_sec >= 1.25s)    │ │
│                           │       └──────────────────────────────────┬───────────────┘ │
│                           │                                          │                 │
│                           │◄──────────────── Trigger Red Flag ───────┘                 │
│                           │                                                            │
│ ┌─────────────────────────▼──────────────────────────────────────────────────────────┐ │
│ │ DBWriteQueue (db_queue.py) - Sequential Thread-Safe SQLite Persistence             │ │
│ └─────────────────────────┬──────────────────────────────────────────────────────────┘ │
└───────────────────────────┼────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
 ┌─────────────────────────┐ ┌─────────────────────────────────┐
 │ SQLite 3 (WAL Mode)     │ │ ./data/evidence/                │
 │ ./cheating_system.db    │ │ - {incident_id}.mp4 (15 FPS)    │
 │ (Table: incidents)      │ │ - {incident_id}.jpg (Snapshot)  │
 └─────────────────────────┘ └─────────────────────────────────┘
```

---

## 2. KIỂM KÊ GIAO DIỆN FRONTEND (FRONTEND INVENTORY)

### 2.1. Các thành phần Runtime Đang Hoạt Động (ACTIVE_RUNTIME)
Toàn bộ các component này được import và render trực tiếp trong cây component React (`src/App.tsx`):

| Tệp nguồn | Vai trò kỹ thuật | Trạng thái phạm vi |
|---|---|---|
| `src/main.tsx` | Khởi tạo ReactDOM và cấu hình root layout | ACTIVE_RUNTIME (Đúng scope) |
| `src/App.tsx` | Điều hướng giữa 2 màn hình: `live-monitor` và `ai-settings`; hiển thị modal video bằng chứng | ACTIVE_RUNTIME (Đúng scope) |
| `src/components/TopNavBar.tsx` | Thanh điều hướng đầu trang, hiển thị trạng thái kết nối backend, chuyển tab và chỉ báo chế độ Offline | ACTIVE_RUNTIME (Đúng scope) |
| `src/components/StreamlinedProctorDashboard.tsx` | Giao diện chính: Khung phát trực tiếp webcam/file video, hiển thị HUD bounding box thời gian thực, bảng danh sách sự cố gần nhất và nút mở modal xem bằng chứng | ACTIVE_RUNTIME (Đúng scope) |
| `src/components/AISettingsView.tsx` | Màn hình cấu hình: Điều chỉnh ngưỡng nhạy điện thoại (`phone_confidence`), thời gian quay đầu (`posture_alert_seconds`), ngưỡng nghi vấn (`suspicion_threshold`), thời lượng RingBuffer (`pre_roll_seconds`, `post_roll_seconds`, `cooldown_seconds`) | ACTIVE_RUNTIME (Đúng scope) |
| `src/components/modals/VideoEvidenceModal.tsx` | Hộp thoại phát lại video bằng chứng MP4 đã trích xuất, hiển thị thông tin vi phạm và các nút "Xác nhận vi phạm", "Bỏ qua", nhập ghi chú | ACTIVE_RUNTIME (Đúng scope) |
| `src/services/api.ts` | Tầng giao tiếp mạng tập trung cho các endpoint REST API (`/api/incidents`, `/api/settings/ai`, `/api/session/reset`) | ACTIVE_RUNTIME (Đúng scope) |
| `src/services/aiModelService.ts` | Quản lý kết nối WebSocket nhị phân `/api/ws/ingest`, mã hóa header 16 bytes, điều tiết áp lực ngược (backpressure) và giải mã payload telemetry | ACTIVE_RUNTIME (Đúng scope) |
| `src/types.ts` | Khai báo kiểu TypeScript chuẩn cho sự cố, cấu hình AI, kết quả nhận diện và các telemetry counter | ACTIVE_RUNTIME (Đúng scope) |

### 2.2. Tài sản Tồn dư Lịch sử (Phân loại REACHABLE_BUT_UNUSED và Đã Xử lý Triệt để trong Sprint 3.1)
Trước Sprint 3.1, các tệp HTML tĩnh và ảnh mẫu sau tồn tại trong thư mục `public/`. Mặc dù không được import bởi mã nguồn React trong `src/`, Vite vẫn phục vụ các tệp tĩnh này tại URL gốc nếu người dùng truy cập trực tiếp (ví dụ: `http://localhost:3000/screens/04-report-protocol.html` hay `/avatars/student_01.jpg`). Do đó, chúng được phân loại kỹ thuật chính xác là **`REACHABLE_BUT_UNUSED`** (Có thể truy cập nhưng không thuộc phạm vi sản phẩm).

Trong Sprint 3.1, toàn bộ các tệp này đã được **XÓA BỎ HOÀN TOÀN** khỏi kho mã nguồn và xác minh tính toàn vẹn:

| Đường dẫn tệp gốc | Loại tài sản cũ | Phân loại kỹ thuật | Trạng thái sau Sprint 3.1 |
|---|---|---|---|
| `public/screens/01-live-dashboard.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/02-room-matrix-evidence.html` | Mockup HTML cũ (Sơ đồ ma trận) | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/03-penalty-modal.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/04-report-protocol.html` | Mockup HTML cũ (Biên bản vi phạm) | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/05-camera-calibration.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/06-ai-settings.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/07-exam-room-setup.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/08-exam-session-creator.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/09-camera-stream-hub.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/10-workflow-diagram.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/11-end-session-modal.html` | Mockup HTML cũ | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/screens/index.html` | Mục lục danh sách mockup | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/avatars/student_01.jpg` đến `student_08.jpg` | Ảnh đại diện thí sinh mẫu | REACHABLE_BUT_UNUSED | **ĐÃ XÓA (Deleted)** |
| `public/cctv/cctv_room_01.jpg` đến `cctv_room_03.jpg` | Ảnh phòng thi tĩnh mẫu | UNREFERENCED_ASSET | Giữ lại (asset tĩnh phụ trợ) |
| `public/evidence/cheat_sheet_violation.jpg` | Ảnh bằng chứng giả lập cũ | UNREFERENCED_ASSET | Giữ lại (asset tĩnh phụ trợ) |
| `public/evidence/paper_exchange_violation.jpg` | Ảnh bằng chứng giả lập cũ | UNREFERENCED_ASSET | Giữ lại (asset tĩnh phụ trợ) |

**Kết quả xác minh thực tế (Kiểm chứng tự động qua `scripts/verify_legacy_assets.py`):**
- Lệnh `npm run build` tạo thư mục xuất xưởng `dist/` không chứa thư mục `screens/` hay `avatars/`; `index.html` là tài liệu HTML duy nhất ở root.
- Yêu cầu HTTP trực tiếp tới các URL cũ (ví dụ `http://localhost:3000/screens/04-report-protocol.html` hay `/avatars/student_01.jpg`):
  `Legacy asset removed; request resolves to generic SPA fallback, not legacy content.` (HTTP 200, Content-Type: text/html, kích thước ~1KB của `index.html` tổng quát; không chứa từ khóa biên bản/sơ đồ phòng thi và không trả MIME/image bytes của avatar cũ).

---

## 3. LUỒNG XỬ LÝ BACKEND 12 BƯỚC (BACKEND PROCESSING FLOW)

Quy trình nhận diện, suy luận và ghi bằng chứng được hiện thực hóa qua 12 bước tuần tự chính xác trong mã nguồn backend:

1. **Thu nhận Khung hình tại Trình duyệt (Client Capture):** Trình duyệt web đọc luồng camera qua `HTMLVideoElement`, trích xuất frame định kỳ bằng `OffscreenCanvas` / Canvas 2D ở tần suất mục tiêu 15 FPS.
2. **Đóng gói Gói tin Nhị phân Client (Binary Framing):** Trình duyệt mã hóa ảnh JPEG, tạo tiêu đề nhị phân 16 bytes gồm `sequence_id` (int64 big-endian) và `monotonic_timestamp` (float64 big-endian) ghép với mảng byte ảnh (`ArrayBuffer`).
3. **Kiểm tra Áp lực ngược (Backpressure Guard):** Trước khi gửi qua WebSocket, client kiểm tra `ws.bufferedAmount > 65536`. Nếu hàng đợi truyền thông tin vượt quá 64 KB, frame sẽ bị hủy (drop) chủ động và tăng counter `client_backpressure_drops`.
4. **Tiếp nhận & Xác thực WebSocket (WebSocket Ingestion & Validation):** Endpoint `/api/ws/ingest` xác thực regex của `source_id` và `session_id`. Nếu kích thước gói tin $< 20$ bytes hoặc $> 3$ MB, gói tin bị từ chối ngay lập tức.
5. **Đẩy Khung hình vào Pipeline 1 (RingBuffer Push):** Server giải mã tiêu đề 16 bytes, đọc ảnh thành mảng `np.ndarray` bằng `cv2.imdecode`. Khung hình được đẩy lập tức vào `VideoRingBuffer.push_frame()` bất kể mô hình AI có đang bận hay không.
6. **Handoff Bất đồng bộ sang Pipeline 2 (Single-Slot Queue):** Server đưa tham chiếu khung hình mới nhất vào `SingleSlotInferenceBuffer.put()`. Nếu slot đã có khung hình cũ đang chờ, khung hình cũ bị thay thế (superseded) ngay lập tức và tăng counter `inference_superseded_frames`.
7. **Kéo Khung hình bởi Daemon Worker (Inference Worker Pull):** Luồng nền `InferenceWorker` liên tục kéo khung hình mới nhất từ slot đệm để tiến hành suy luận học sâu.
8. **Ước lượng Tư thế & Bám vết (YOLO Pose & ByteTrack):** Khung hình được đưa qua `yolo11m-pose.pt`. Mô hình trả về 17 điểm khung xương và bám vết đối tượng gán `track_id`. Tọa độ các điểm được làm mượt qua bộ lọc EMA (`KeypointSmoother`, $\alpha = 0.75$).
9. **Nhận diện Điện thoại & Phân tích Hình học Tư thế Đầu (YOLO Phone & Heuristics):** Mô hình `phone_detector_v5.pt` phát hiện điện thoại di động với ngưỡng `phone_conf = 0.35`. Giải thuật hình học tính toán điểm nghi vấn tư thế đầu từ tỷ lệ vị trí mắt/mũi/tai COCO.
10. **Theo dõi Liên tục Thời gian & Leo thang Cảnh báo (Temporal Tracking):**
    - Nếu góc quay đầu bất thường nhưng duy trì $< 1.25$s: Đánh dấu trạng thái nghi vấn Cờ Vàng (`yellow`), chỉ hiển thị HUD.
    - Nếu phát hiện điện thoại HOẶC thời gian quay đầu liên tục $\ge 1.25$s: Kích hoạt Cờ Đỏ (`red`).
11. **Kích hoạt & Kết xuất Clip Bằng chứng (Clip Stitching & Resampling):** Khi có cờ Đỏ, `VideoRingBuffer.trigger_incident()` khóa đoạn video từ `trigger_time - 5.0s` và tiếp tục thu thập khung hình trong `10.0s` tiếp theo. Một worker thread độc lập thực hiện resampling khung hình trên lưới thời gian thực chính xác để tạo video MP4 phát chuẩn tốc độ 1.0x (15 FPS), trích xuất snapshot JPEG tại thời điểm vi phạm cao nhất, và xác thực tính toàn vẹn tệp bằng OpenCV (`validate_video_file`).
12. **Ghi Dữ liệu Tuần tự vào SQLite (Sequential DB Persistence):** Sau khi tệp MP4 đã được ghi đĩa và xác thực thành công, tác vụ lưu trữ được chuyển vào `DBWriteQueue`. Luồng ghi duy nhất thực hiện chèn bản ghi vào bảng `incidents` trong cơ sở dữ liệu SQLite 3 chế độ WAL, đảm bảo không xảy ra xung đột khóa bảng (database locked).

---

## 4. LƯỢC ĐỒ CƠ SỞ DỮ LIỆU THỰC TẾ (SQLITE DATABASE SCHEMA)

Kiểm tra trực tiếp tệp `./cheating_system.db` và mã nguồn `backend/models.py`:
- **Chế độ hoạt động:** SQLite 3 với `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA foreign_keys=ON;`.
- **Số lượng bảng:** Đúng **01 bảng duy nhất** (`incidents`).
- **Tổng số cột:** 14 cột.
- **Ranh giới bảo mật danh tính:** Hoàn toàn **KHÔNG CÓ** bất kỳ cột nào chứa tên thí sinh, số báo danh (SBD), mã số CCCD, ảnh đại diện, vector đặc trưng khuôn mặt (FaceNet embeddings) hay chữ ký số.

### Bảng cấu trúc chi tiết (`incidents`):

| Tên cột | Kiểu dữ liệu | Nullable | Mặc định | Ý nghĩa kỹ thuật |
|---|---|---|---|---|
| `id` | VARCHAR(100) | NO | Primary Key | Mã định danh sự cố duy nhất dạng chuỗi: `inc_{timestamp}_{uuid}` |
| `source_id` | VARCHAR(100) | NO | `'webcam_local'` | Nguồn video đầu vào (ví dụ: `webcam_local`, `cam_01`) |
| `track_id` | INTEGER | YES | NULL | Mã theo dõi ẩn danh cơ học tạm thời gán bởi ByteTrack |
| `violation_type` | VARCHAR(50) | NO | None | Loại vi phạm: Duy nhất `'PHONE'` hoặc `'HEAD_TURNING'` |
| `confidence` | REAL | NO | `0.90` | Điểm tin cậy nhận diện: Chuẩn hóa xác suất thô [0.0 - 1.0] trong DB/API; validator tương thích ngược chấp nhận thang 100 bằng cách chia 100; Frontend nhân 100 khi hiển thị % |
| `level` | VARCHAR(20) | NO | `'red'` | Mức độ nghiêm trọng: `'yellow'` hoặc `'red'` |
| `detected_at` | TIMESTAMP | NO | `utcnow` | Mốc thời gian UTC hệ thống phát hiện vi phạm |
| `clip_started_at` | TIMESTAMP | YES | NULL | Mốc thời gian UTC bắt đầu đoạn clip bằng chứng (pre-roll) |
| `clip_ended_at` | TIMESTAMP | YES | NULL | Mốc thời gian UTC kết thúc đoạn clip bằng chứng (post-roll) |
| `video_path` | VARCHAR(500) | YES | NULL | Đường dẫn tĩnh phục vụ video clip: `/evidence/{id}.mp4` |
| `snapshot_path` | VARCHAR(500) | YES | NULL | Đường dẫn tĩnh phục vụ ảnh chụp: `/evidence/{id}.jpg` |
| `status` | VARCHAR(20) | NO | `'pending'` | Trạng thái xử lý: `'pending'`, `'confirmed'`, `'dismissed'` |
| `proctor_notes` | TEXT | YES | NULL | Ghi chú văn bản của giám thị khi xem lại sự cố |
| `created_at` | TIMESTAMP | NO | `utcnow` | Mốc thời gian UTC bản ghi được tạo vào CSDL |

#### Lưu ý Kỹ thuật về Tính An toàn và Toàn vẹn CSDL (Technical Caveats):
1. **Bản chất của SQLite WAL Mode:** Chế độ Write-Ahead Logging (WAL) cùng `PRAGMA synchronous=NORMAL;` được thiết kế nhằm tối ưu hóa tính đồng thời (concurrency) trên hệ thống tệp cục bộ, cho phép nhiều luồng đọc (FastAPI query) và một luồng ghi tuần tự (`DBWriteQueue`) hoạt động song song mà không khóa lẫn nhau (tránh triệt để lỗi `sqlite3.OperationalError: database is locked`).
2. **Giới hạn Bảo vệ khi Sập nguồn (Crash vs Power Loss):** WAL mode đảm bảo khả năng phục hồi sau sự cố phần mềm (crash recovery) và ngăn ngừa hư hại cấu trúc tệp CSDL (corruption-free). Tuy nhiên, với chế độ `synchronous=NORMAL`, nếu máy trạm giám thị bị mất điện đột ngột ở cấp phần cứng (hard power loss), giao dịch mới nhất đang nằm trong bộ đệm WAL chưa kịp sync xuống đĩa từ tính có thể bị mất.
3. **Phân định Ranh giới Bảo mật:** WAL mode **KHÔNG PHẢI** là cơ chế mã hóa hay bảo mật mạng; dữ liệu được bảo vệ dựa trên nguyên tắc kiến trúc Offline 100% không lộ cổng ra Internet và quyền truy cập tập tin cục bộ của hệ điều hành.

---

## 5. THỰC TẾ TÍCH HỢP MÔ HÌNH HỌC SÂU (MODEL INTEGRATION FACTS)

Thông tin được trích xuất trực tiếp từ các tệp checkpoint trọng số nhị phân trong thư mục `model/weights/`:

### 5.1. Mô hình Phát hiện Điện thoại (`phone_detector_v5.pt`)
- **Đường dẫn tệp:** `model/weights/phone_detector_v5.pt`
- **Kích thước tệp:** 19,245,082 bytes (~18.35 MB)
- **Mã băm SHA-256:** `23FA698727A49CB8BA7D260C1AC13F01D4D27E8726E97AA3D8FEF992AD5E19C2`
- **Kiến trúc mô hình:** YOLOv8/YOLO11 Detection Model (Ultralytics framework)
- **Danh sách nhãn phân loại (Classes):** Đúng 01 class duy nhất: `{0: 'phone'}`
- **Epoch ghi nhận trong checkpoint:** `-1` (đã qua bước xuất tối ưu `strip_optimizer`)
- **Tham số huấn luyện lưu trong metadata:** `imgsz: 960`, `batch: 6`, `data: 'data_phone.yaml'`
- **Ngưỡng tin cậy vận hành runtime:** Mặc định `0.35` (35%), cấu hình thông qua `/api/settings/ai`
- **Lưu ý phân loại bằng chứng:** Các chỉ số huấn luyện cũ trong tài liệu (`mAP@0.5 = 76.92%`) là `TRAINING_VALIDATION_ONLY`. Chưa có kiểm định độc lập do thiếu tập dữ liệu gốc (Blocker D-01).

### 5.2. Mô hình Ước lượng Tư thế Khung xương (`yolo11m-pose.pt`)
- **Đường dẫn tệp:** `model/weights/yolo11m-pose.pt`
- **Kích thước tệp:** 42,459,307 bytes (~40.49 MB)
- **Mã băm SHA-256:** `29B17EAF3A3117CBEA906090DBEDF9159F7C6A49DB58EC8B99ED2DFDE1CF6EB2`
- **Kiến trúc mô hình:** YOLO11m Pose Estimation Model
- **Danh sách nhãn phân loại (Classes):** Đúng 01 class: `{0: 'person'}`
- **Cấu trúc điểm mốc khung xương (Keypoint shape):** `[17, 3]` (17 điểm COCO: tọa độ x, y và độ tin cậy)
- **Bộ lọc làm mượt (Smoothing filter):** Exponential Moving Average (`KeypointSmoother`, $\alpha = 0.75$) được thiết kế nhằm hạn chế rung giật pixel (landmark jitter) giữa các frame liên tiếp; đây là cơ chế thiết kế (design intention), chưa có đo lường thực nghiệm định lượng (ablation study) trên tập nhãn chuẩn.
- **Thuật toán bám vết:** ByteTrack. Trường `track_id` là định danh kỹ thuật trong luồng xử lý để liên kết các detection qua thời gian, không đại diện cho danh tính thực tế của thí sinh.

### 5.3. Quy tắc Xác định Hành vi Quay đầu Nhìn bài (Head-Turning Semantics)
- **Phân tích hình học điểm mốc đầu:** So sánh tỷ lệ khoảng cách giữa điểm mũi (`Nose`), hai mắt (`Left Eye`, `Right Eye`) và hai tai (`Left Ear`, `Right Ear`), tính ra độ lệch tâm chuẩn hóa `offset_sym` và tỷ lệ khoảng cách `sym_ratio`.
- **Công thức suy diễn `turn_deg = disp_deg`:**
  ```python
  disp_deg = (
      detected_yaw_deg
      if (head_turn_score > 0.15 and detected_yaw_deg > 0)
      else (head_turn_score * 45.0 if head_turn_score > 0.15 else 0.0)
  )
  ```
  *(Ghi chú bắt buộc: Tên trường `turn_deg` là tên trường tương thích giao diện; giá trị là chỉ số trực quan hóa suy ra từ heuristic, không phải phép đo góc vật lý).*
- **Ngưỡng nghi vấn (`suspicion_threshold`):** Mặc định `0.50`. Đây là **Điểm số Nghi vấn Tư thế Chuẩn hóa (Normalized Posture Suspicion Score)** không thứ nguyên trong miền giá trị $[0.0, 1.0]$ tính từ tổ hợp tỷ lệ hình học keypoint COCO; **không phải là góc độ hay radian**.
- **Quy tắc bảo vệ tính liên tục thời gian (Temporal Continuity Guard):** Đòi hỏi hành vi quay đầu phải duy trì liên tục qua thời gian thực $\ge 1.25$ giây (`posture_alert_seconds`) để leo thang cờ Đỏ, loại trừ hiện tượng giật cục do cử động vô thức tức thời. *(Trạng thái kiểm chứng: Đã vượt qua synthetic unit tests trong backend test suite; chưa có holdout video benchmark thực tế - Blocker D-03)*.

---

## 6. THỰC TẾ XUẤT CLIP BẰNG CHỨNG (EVIDENCE CLIP EXTRACTION FACTS)

Toàn bộ quy trình trích xuất clip tuân thủ các thông số kỹ thuật được xác minh từ `backend/services/ring_buffer.py`:

- **Cấu hình thời lượng cửa sổ:**
  - `pre_roll_seconds`: Mặc định `5.0` giây trước thời điểm vi phạm.
  - `post_roll_seconds`: Mặc định `10.0` giây sau thời điểm vi phạm.
  - `cooldown_seconds`: Mặc định `6.0` giây giữa hai lần kích hoạt liên tiếp của cùng đối tượng và loại vi phạm.
  - Tổng thời lượng clip điển hình: Khoảng **15.0 giây**.
- **Định dạng và Mã hóa:**
  - Định dạng container: MP4 (`.mp4`)
  - Video Codec FourCC: Ưu tiên mã hóa `avc1` (H.264), tự động chuyển đổi sang `mp4v` nếu codec không sẵn sàng trên hệ điều hành.
  - Định dạng ảnh chụp nhanh: JPEG (`.jpg`) trích xuất từ khung hình có độ tin cậy/điểm nghi vấn cao nhất.
- **Tốc độ khung hình (FPS) và Cơ chế Resampling Tự nhiên:**
  - Tần suất khung hình mục tiêu xuất ra: **15.0 FPS**.
  - **Kỹ thuật Time-Grid Resampling:** Do tốc độ mạng hoặc phần cứng máy trạm có thể biến động, các frame lưu trong bộ đệm được nội suy tái lập trên một lưới thời gian thực cách đều chính xác $1/15$ giây. Cơ chế này đã được chứng minh qua kiểm thử kiểm soát giúp video phát chuẩn tốc độ tự nhiên 1.0x (không bị tua nhanh timelapse). *(Caveat: Đây là phép đo trong điều kiện kiểm thử có kiểm soát; nếu phần cứng máy trạm quá tải nghiêm trọng dẫn tới sụt giảm frame sâu từ trước khi vào buffer, clip có thể bị khuyết một số frame gốc)*.
- **Kiểm tra Tính toàn vẹn Tập tin (File Integrity Check):**
  - Hàm `validate_video_file()` kiểm tra bắt buộc: kích thước tập tin $> 0$ bytes và OpenCV có thể mở (`VideoCapture.isOpened()`) cũng như đọc thành công ít nhất một frame (`ret == True`).
  - Chỉ những clip vượt qua kiểm tra này mới được đưa vào hàng đợi ghi CSDL.
- **Khóa Cooldown Đa mục tiêu (Multi-Target Cooldown Key):**
  - Khóa cooldown được kết hợp theo bộ 4 giá trị: `(session_id, source_id, str(track_id), violation_type)`.
  - Cơ chế này đảm bảo: Nếu thí sinh A vi phạm `HEAD_TURNING` và bị khóa cooldown 6.0s, thí sinh B vi phạm hoặc thí sinh A vi phạm `PHONE` vẫn được kích hoạt clip bình thường mà không bị bỏ sót.

---

## 7. ĐỐI SOÁT API VÀ WEBSOCKET CONTRACT (API CONTRACT MATRIX)

Kiểm tra toàn bộ các router được đăng ký trong `backend/main.py`:

| Giao thức / Method | Đường dẫn Endpoint | Mô hình Yêu cầu (Request) | Mô hình Trả về (Response) | Bên tiêu thụ (Consumer) | Mã kiểm thử bảo vệ | Đánh giá Scope |
|---|---|---|---|---|---|---|
| **GET** | `/api/health` | None | `{"status", "mode", "database", "evidence_storage"}` | Giám thị / Hệ thống giám sát | TestClient / Manual | Đúng scope |
| **GET** | `/api/incidents` | Query: `source_id`, `violation_type`, `level`, `status`, `limit`, `skip` | `List[IncidentResponse]` | Frontend Dashboard (`src/services/api.ts`) | `test_01`, `test_02`, `test_14` | Đúng scope |
| **PATCH** | `/api/incidents/{incident_id}/confirm` | Body: `IncidentConfirmRequest` (`status`, `notes`) | `IncidentResponse` | Frontend Modal (`src/services/api.ts`) | `test_03_confirm_incident_updates_db` | Đúng scope |
| **GET** | `/api/settings/ai` | None | `AISettingsSchema` | Frontend Settings (`src/services/api.ts`) | `test_10_settings_endpoint_syncs_ring_buffer` | Đúng scope |
| **POST** | `/api/settings/ai` | Body: `AISettingsSchema` | `AISettingsSchema` | Frontend Settings (`src/services/api.ts`) | `test_10` | Đúng scope |
| **POST** | `/api/session/reset` | Query: `session_id` | `SessionResetResponse` | Frontend Reconnect / Cleanup | `test_21`, `test_26`, `test_28` | Đúng scope |
| **GET** | `/api/session/telemetry` | Query: `session_id` | `SessionTelemetryResponse` | Frontend Dashboard / Telemetry Monitor | `test_27`, `test_28` | Đúng scope |
| **GET** | `/api/status` | None | `AIStatusResponse` | TopNavBar Status Indicator | `test_11_status_reports_correct_device` | Đúng scope |
| **GET** | `/api/stream` | None | `StreamingResponse` (multipart/x-mixed-replace) | Trình duyệt / External MJPEG Player | Manual verification | Phụ trợ (Đúng scope) |
| **WS** | `/api/ws/ingest` | Binary: 16 bytes header + JPEG image bytes | JSON: `WebSocketDetectionPayload` + Telemetry | Frontend Capture Loop (`src/services/aiModelService.ts`) | `test_22` đến `test_28` | Đúng scope |
| **GET** | `/evidence/{filename}` | Path: `filename` (Static Mount) | Binary: Video MP4 / JPEG Snapshot | VideoEvidenceModal (`src/components/modals/VideoEvidenceModal.tsx`) | `test_08`, `test_31` | Canonical Route duy nhất mặc định (Phòng thủ chống path traversal) |
| **GET** | `/api/clips/{filename}` | Path: `filename` | `FileResponse` (video/mp4) | Tương thích ngược cũ (Tắt mặc định qua `ENABLE_LEGACY_CLIPS=false`) | `test_31` | Legacy Clips Guard (Mặc định 404, ẩn khỏi OpenAPI; có basename defense khi bật) |
| **POST** | `/api/detect/frame` | Body: `FrameDetectionRequest` (Base64) | `FrameDetectionResponse` | Tương thích ngược cũ (Tắt mặc định qua `ENABLE_DEPRECATED_INGEST=false`) | `test_04`, `test_29` | Deprecated Guard (Mặc định 404, ẩn khỏi OpenAPI) |
| **POST** | `/api/test/trigger_incident` | Query: `violation_type`, `level`, `track_id`, `session_id` | `TestTriggerIncidentResponse` | Test harness / CI Pipeline (Tắt mặc định qua `ENABLE_TEST_ENDPOINTS=false`) | `test_01`, `test_25`, `test_29` | Protected Test Endpoint (Mặc định 404, ẩn khỏi OpenAPI) |

---

## 8. PHÂN LOẠI VÀ KIỂM CHỨNG DỮ LIỆU TELEMETRY (TELEMETRY EVIDENCE CLASSIFICATION)

Nhằm đảm bảo tính liêm chính khoa học, mọi số liệu xuất hiện trong tài liệu và báo cáo đều được phân định rạch ròi theo 5 cấp độ bằng chứng:

| Nhãn phân loại | Bản chất kỹ thuật | Quy tắc sử dụng trong Báo cáo KHKT |
|---|---|---|
| **`MEASURED_REAL_E2E`** | Số liệu đo đạc thực nghiệm từ phiên chạy thực tế của hệ thống hoàn chỉnh (End-to-End). | **ĐƯỢC PHÉP ĐƯA VÀO BÁO CÁO.** Phải ghi rõ điều kiện phần cứng máy trạm (CPU, GPU, RAM) và cấu hình phiên thử nghiệm. |
| **`MEASURED_CONTROLLED_TRIGGER`** | Số liệu đo đạc trong kịch bản kiểm thử có kiểm soát (kích hoạt sự cố nhân tạo để đo thời gian xuất clip, đo độ trễ ghi DB). | **ĐƯỢC PHÉP ĐƯA VÀO BÁO CÁO.** Bắt buộc ghi rõ đây là thử nghiệm kích hoạt có kiểm soát (Stress/Latency Test). |
| **`SYNTHETIC_FIXTURE`** | Dữ liệu giả lập sinh tự động trong bộ test để kiểm tra logic rẽ nhánh, kiểm tra toán học hoặc kiểm tra biên lỗi. | **KHÔNG ĐƯỢC PHÉP ĐƯA VÀO BÁO CÁO** dưới dạng kết quả thực nghiệm hệ thống. Chỉ được đề cập trong phần "Quy trình kiểm thử phần mềm". |
| **`CONFIG_VALUE`** | Các giá trị tham số cấu hình tĩnh hoặc mặc định trong mã nguồn (`pre_roll = 5.0s`, `phone_conf = 0.35`). | **ĐƯỢC PHÉP ĐƯA VÀO BÁO CÁO** trong mục "Thông số thiết kế và Cài đặt giải thuật". Phải ghi rõ là giá trị cấu hình danh định. |
| **`UNVERIFIED_CLAIM`** | Các tuyên bố cảm tính, các số liệu từ tài liệu cũ không còn nguồn kiểm chứng hoặc chưa có tập dữ liệu nhãn chuẩn. | **BỊ LOẠI BỎ KHỎI BÁO CÁO.** |

### 8.1. Hệ thống 8 Bất biến Kỹ thuật Telemetry (The 8 Telemetry Invariants)
Để kiểm chứng luồng dữ liệu thời gian thực và ngăn ngừa tình trạng trôi số liệu hay rò rỉ bộ nhớ, hệ thống thiết lập và kiểm tra tự động **8 Bất biến Toán học & Vận hành**, được chia thành 3 nhóm cơ sở:

#### Nhóm 1: Ràng buộc Bảo toàn Khung hình (Conservation Laws)
1. **Bất biến 2 (Client Frame Conservation):**  
   Khung hình gửi đi cộng với số khung hình bị hủy do áp lực ngược không bao giờ vượt quá số khung hình đã mã hóa thành công:  
   $$\text{sent\_frames} + \text{client\_backpressure\_drops} \le \text{capture\_encoded\_frames}$$
2. **Bất biến 6 (Inference Queue Strict Conservation - Đẳng thức Bảo toàn Hàng đợi Suy luận):**  
   Toàn bộ khung hình được đưa vào hàng đợi suy luận bắt buộc phải nằm ở 1 trong 3 trạng thái: đã suy luận xong, bị thay thế bởi khung mới hơn (superseded), hoặc đang nằm trong slot chờ (pending). Không thất thoát khung hình nào:  
   $$\text{inference\_processed\_frames} + \text{inference\_superseded\_frames} + \text{inference\_pending\_frames} \equiv \text{inference\_submitted\_frames}$$

#### Nhóm 2: Ràng buộc Tỷ lệ và Thứ tự Luồng Xử lý (Rate & Ordering Constraints)
3. **Bất biến 1 (Client Capture Validity):** Số khung hình mã hóa thành công không vượt quá số lần thử chụp từ camera:  
   $$\text{capture\_encoded\_frames} \le \text{capture\_attempts}$$
4. **Bất biến 3 (Network Ingress):** Số gói tin máy chủ nhận được không vượt quá số gói tin client đã gửi:  
   $$\text{server\_packets\_received} \le \text{sent\_frames}$$
5. **Bất biến 4 (Payload Decode):** Số khung hình giải mã thành công không vượt quá số gói tin tiếp nhận:  
   $$\text{server\_frames\_decoded} \le \text{server\_packets\_received}$$
6. **Bất biến 5 (Pipeline Handoff):** Số khung hình chuyển giao sang suy luận không vượt quá số khung hình đã giải mã:  
   $$\text{inference\_submitted\_frames} \le \text{server\_frames\_decoded}$$
7. **Bất biến 7 (Result Egress):** Số thông điệp kết quả AI phát đi không vượt quá số khung hình đã suy luận:  
   $$\text{result\_messages\_sent} \le \text{inference\_processed\_frames}$$
8. **Bất biến 8 (Client Result Ingress):** Số kết quả client nhận được không vượt quá số kết quả máy chủ đã gửi:  
   $$\text{result\_messages\_received} \le \text{result\_messages\_sent}$$

#### Nhóm 3: Tiêu chí Chấp nhận Vận hành (Operational Acceptance Criteria)
- **Tính Tăng Đơn điệu (Monotonicity):** Tất cả các bộ đếm telemetry tích lũy chỉ tăng hoặc giữ nguyên theo thời gian thực ($c_{t+1} \ge c_t$), không bao giờ giảm trong cùng một phiên làm việc.
- **Tính Cô lập & Tái lập (Session Clean Slate):** Khi gửi lệnh `/api/session/reset`, toàn bộ các bộ đếm trên cả Client và Server lập tức trở về 0 tại $t=0$, đảm bảo phiên thi mới không bị ảnh hưởng bởi phiên trước.
- **Giới hạn Độ trễ Tích lũy (Backlog Depth Bound):** Hàng đợi `SingleSlotInferenceBuffer` duy trì độ sâu hàng đợi $\le 1$ ở mọi thời điểm ($\text{inference\_pending\_frames} \in \{0, 1\}$).

*(Toàn bộ các bất biến này được kiểm thử tự động tại `backend/tests/test_refactored_system.py:test_28_session_telemetry_invariants_and_isolation` và `src/services/__tests__/test_telemetry_contract.ts`)*.

---

## 9. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG THỰC TẾ (RAW TEST OUTPUTS)

Tất cả các lệnh kiểm thử sau được thực thi trực tiếp trên máy trạm tại commit `8e4a855`:

### 9.1. Bộ Kiểm thử Đánh giá Độc lập (Evaluation Harness Tests)
- **Lệnh thực thi:** `.venv\Scripts\python.exe -m unittest -v scripts/evaluation/tests/test_evaluation_harness.py`
- **Thời gian thực thi:** 0.241 giây
- **Kết quả:** **22 / 22 bài kiểm thử ĐẠT (OK)**
- **Nội dung kiểm chứng:** Kiểm tra cấu trúc phân giải YAML, kiểm tra tính hợp lệ của hộp nhãn biên cạnh, từ chối nhãn NaN/Inf/kích thước 0, kiểm tra tính nhất quán mã băm fingerprint tập dữ liệu, bảo vệ rò rỉ dữ liệu giữa tập train/val/test, thuật toán tính Average Precision (AP), thuật toán bóc tách khoảng thời gian sự kiện vi phạm (event union & one-to-one matching), độ sai lệch thời gian phát hiện (onset error).

### 9.2. Bộ Kiểm thử Hồi quy Backend (Backend Regression Tests)
- **Lệnh thực thi:** `.venv\Scripts\python.exe -m unittest -v backend.tests.test_refactored_system`
- **Thời gian thực thi:** 9.146 giây
- **Kết quả:** **31 / 31 bài kiểm thử ĐẠT (OK)**
- **Nội dung kiểm chứng:**
  - `test_01` & `test_02`: Tạo sự cố cờ đỏ `PHONE` và `HEAD_TURNING` ghi đúng CSDL SQLite.
  - `test_03`: Cập nhật trạng thái sự cố (`confirmed`, `dismissed`) qua API PATCH.
  - `test_04`: Endpoint `/api/detect/frame` xử lý frame Base64 (khi bật flag tương thích).
  - `test_05` & `test_06`: Bộ đệm RingBuffer kích hoạt và ghi video MP4 có độ dài thực tế $> 0$ bytes.
  - `test_07`: Giới hạn tốc độ cooldown (6.0s) ngăn chặn spam tạo clip trùng lặp.
  - `test_08`: Static mount `/evidence` phục vụ video clip MP4.
  - `test_09`: Endpoint `/api/clips/{filename}` trả về tệp video hợp lệ.
  - `test_10`: Đồng bộ cấu hình AI giữa `/api/settings/ai` và RingBuffer.
  - `test_11` & `test_12`: Trạng thái hệ thống và xử lý lỗi ngắt kết nối an toàn.
  - `test_13`: Kiểm tra tính toàn vẹn tệp MP4 bằng OpenCV.
  - `test_14`: Xác thực cấu trúc JSON trả về tuân thủ Pydantic schema.
  - `test_15`: Ghi dữ liệu đồng thời từ nhiều luồng vào SQLite WAL qua hàng đợi tuần tự.
  - `test_16`: Xử lý mốc thời gian ISO 8601 múi giờ UTC.
  - `test_17` & `test_18`: Kiểm tra cấu hình CORS và kích thước frame tùy ý.
  - `test_19` & `test_20`: Làm sạch bộ đệm khi đóng phiên và ngăn chặn path traversal.
  - `test_21`: Endpoint `/api/session/reset` làm sạch bộ nhớ tạm.
  - `test_22` đến `test_28`: Kiểm tra toàn diện luồng WebSocket nhị phân: unpack header 16-byte, xác thực sequence, bảo vệ kích thước gói tin, cô lập phiên làm việc, mốc thời gian monotonic máy chủ và các bất biến toán học telemetry.
  - `test_29`: Kiểm chứng cơ chế bảo vệ endpoint kiểm thử (`POST /api/test/trigger_incident` trả về 404 và ẩn khỏi OpenAPI khi tắt flag; trả về 200 khi bật flag) và bảo vệ ingest cũ (`POST /api/detect/frame`).
  - `test_30`: Kiểm chứng từ vựng sự cố chuẩn (`PHONE`, `HEAD_TURNING`), chuyển đổi tương thích nhãn cũ `CHEATING_POSTURE` -> `HEAD_TURNING`, và chuẩn hóa độ tin cậy `confidence` [0.0 - 1.0], từ chối `NaN`/`Inf`/`> 100.0`.
  - `test_31`: Kiểm chứng Static Mount `/evidence/{filename}` là canonical route phục vụ video/ảnh; route legacy mặc định bị tắt; các payload traversal được liệt kê đã bị chặn trong bộ kiểm thử.

### 9.3. Kiểm thử và Biên dịch Giao diện Giám thị (Frontend Verification)
- **Kiểm tra Kiểu Tĩnh TypeScript:**
  - Lệnh thực thi: `npx tsc --noEmit`
  - Kết quả: **0 LỖI (Exit Code 0)** — Toàn bộ contract telemetry và state management đều tuân thủ nghiêm ngặt strict type-checking, không sử dụng `@ts-ignore` hay `any`.
- **Kiểm thử Đơn vị Telemetry Contract:**
  - Lệnh thực thi: `npx tsx src/services/__tests__/test_telemetry_contract.ts`
  - Kết quả: **10 / 10 assertions ĐẠT (OK)** — Xác minh hàm phân giải payload WebSocket trích xuất đầy đủ 8 telemetry counter và bảo toàn giá trị chính xác.
- **Biên dịch Xuất xưởng Sản xuất (Production Build):**
  - Lệnh thực thi: `npm run build` (`vite build`)
  - Thời gian thực thi: 1.77 giây
  - Kết quả: **BIÊN DỊCH THÀNH CÔNG (Exit Code 0)**
  - Tập tin đóng gói xuất xưởng:
    - `dist/index.html`: 0.88 kB (gzip: 0.49 kB) — Sạch bóng CDN Google Fonts.
    - `dist/assets/index-*.css`: 56.54 kB (gzip: 10.33 kB)
    - `dist/assets/index-*.js`: 250.90 kB (gzip: 74.49 kB)

---

## 10. BẢNG ĐĂNG KÝ TUYÊN BỐ KỸ THUẬT VÀ NGUỒN BẰNG CHỨNG (CLAIM REGISTRY)

| Mã Claim | Nội dung Tuyên bố Kỹ thuật | Đường dẫn Bằng chứng Xác minh | Loại bằng chứng | Mức độ xác minh | Đưa vào Báo cáo KHKT |
|---|---|---|---|---|---|
| **CLM-ARCH-01** | Hệ thống vận hành Offline On-Premise trên localhost, không phụ thuộc Cloud hay CDN ngoài trong phạm vi đã kiểm thử. | `backend/main.py`, `src/services/api.ts`, `index.html` | Code Inspection | Đã xác minh | **CHO PHÉP** |
| **CLM-ARCH-02** | Cơ sở dữ liệu sử dụng SQLite 3 với chế độ WAL và Foreign Keys bật tự động trên mỗi kết nối. | `backend/database.py:L26-34` | Code Inspection | Đã xác minh | **CHO PHÉP (Kèm caveat crash vs power loss)** |
| **CLM-DB-01** | Bảng CSDL `incidents` được thiết kế ẩn danh, không có cột danh tính (Tên, SBD, CCCD, FaceNet). | `backend/models.py:L27-72`, `./cheating_system.db` | Schema Query | Đã xác minh | **CHO PHÉP** |
| **CLM-DB-02** | Thao tác ghi CSDL được điều phối qua hàng đợi tuần tự luồng an toàn `DBWriteQueue`, ngăn ngừa lỗi khóa bàn cờ. | `backend/services/db_queue.py`, `test_15` | Test Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-MODEL-01** | Mô hình `phone_detector_v5.pt` (~19.2 MB) chỉ phân loại 1 class duy nhất: `{0: 'phone'}`. | `model/weights/phone_detector_v5.pt` | Checkpoint Inspection | Đã xác minh | **CHO PHÉP** |
| **CLM-MODEL-02** | Mô hình `yolo11m-pose.pt` (~42.5 MB) ước lượng 17 điểm mốc COCO và gán track ID qua ByteTrack. | `model/weights/yolo11m-pose.pt`, `model/exam_analyzer.py` | Code Inspection | Đã xác minh | **CHO PHÉP** |
| **CLM-MODEL-03** | Điểm số mAP@0.5 = 76.92% của mô hình điện thoại là kết quả kiểm định độc lập trên tập test thực tế. | `DOCUMENTATION.md:L23-26` | Audit Finding | Chưa xác minh | **BÁC BỎ (Ghi chú CAVEAT: chỉ là training-validation metric, BLOCKED_D02)** |
| **CLM-PIPE-01** | Hệ thống tách rời hai pipeline: Pipeline 1 (RingBuffer) thu nhận 15 FPS tách biệt với tốc độ suy luận của Pipeline 2. | `backend/routers/ai_engine.py`, `backend/services/inference_worker.py` | Code Inspection | Đã xác minh | **CHO PHÉP** |
| **CLM-PIPE-02** | Hàng đợi suy luận `SingleSlotInferenceBuffer` duy trì backlog depth $\le 1$, tự động thay thế frame cũ để ngăn ngừa độ trễ tích lũy. | `backend/services/inference_worker.py`, `test_28` | Test Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-CLIP-01** | Video bằng chứng tự động trích xuất gồm khoảng 5s pre-roll và 10s post-roll, tổng thời lượng ~15s (theo cấu hình danh định). | `backend/services/ring_buffer.py:L107-109`, `test_05` | Test Verified | Đã xác minh | **CHO PHÉP (Ghi rõ cấu hình danh định)** |
| **CLM-CLIP-02** | Video MP4 được nội suy trên lưới thời gian thực (time-grid resampling) đảm bảo tốc độ phát 1.0x tự nhiên. | `backend/services/ring_buffer.py:L286-350` | Code Inspection | Đã xác minh | **CHO PHÉP (Kèm caveat kiểm thử có kiểm soát)** |
| **CLM-CLIP-03** | Tập tin video MP4 được kiểm tra tính toàn vẹn bằng OpenCV trước khi lưu bản ghi vào CSDL. | `backend/services/ring_buffer.py:L47-60`, `test_13` | Test Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-TELE-01** | Các bộ đếm telemetry tuân thủ nghiêm ngặt 8 bất biến kỹ thuật và cô lập giữa các phiên trong các trường hợp đã kiểm thử. | `backend/routers/ai_engine.py`, `test_28` | Test Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-FE-01** | Giao diện giám thị hiển thị trực tiếp bounding box, mức độ cảnh báo Cờ Vàng/Cờ Đỏ và danh sách sự cố. | `src/components/StreamlinedProctorDashboard.tsx` | UI Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-FE-02** | Giám thị có thể xác nhận (`confirmed`) hoặc bỏ qua (`dismissed`) sự cố trực tiếp trên giao diện và lưu vào SQLite. | `src/components/modals/VideoEvidenceModal.tsx`, `test_03` | Test Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-FE-03** | Frontend tuân thủ strict typecheck (`tsc --noEmit`), không phát hiện lỗi trong các trường hợp đã kiểm thử. | `src/services/aiModelService.ts`, `src/types.ts` | Compiler Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-SEC-01** | Đường dẫn phục vụ video/ảnh bằng chứng phòng thủ chống tấn công duyệt thư mục trái phép (`path traversal`): route legacy mặc định bị tắt; các payload traversal được liệt kê đã bị chặn trong bộ kiểm thử. | `backend/main.py`, `backend/routers/ai_engine.py`, `test_31` | Test Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-GUARD-01** | Endpoint kiểm thử, ingest cũ và clips legacy được bảo vệ bằng feature flags, trả về 404 và ẩn khỏi OpenAPI trong môi trường sản xuất mặc định. | `backend/main.py`, `backend/routers/ai_engine.py`, `test_29`, `test_31` | Test Verified | Đã xác minh | **CHO PHÉP** |
| **CLM-SEM-01** | Độ tin cậy `confidence` canonical là xác suất thô [0.0 - 1.0], chấp nhận (1.0 - 100.0] ở normalization path; ngưỡng `suspicion_threshold` là điểm số không thứ nguyên [0.0 - 1.0]. | `backend/schemas.py`, `backend/services/inference_worker.py`, `test_30` | Test Verified | Đã xác minh | **CHO PHÉP (Kèm residual risk GAP-SEM-01)** |
| **CLM-LINEAGE-01** | Tệp trọng số triển khai `phone_detector_v5.pt` có cùng SHA-256 (`23fa698727...`) với artifact `best.pt` được xác định trong run `phone_detector_v5` (đối chiếu đồng nhất artifact bằng SHA-256). | `reports/evidence/training_lineage/lineage_manifest.json` | Hash Verification | Đã xác minh | **CHO PHÉP** |
| **CLM-LINEAGE-02** | Dataset lịch sử `phone_merged` gồm 2.961 ảnh và 3.706 phone boxes (splits: 2.434 train, 382 val, 145 internal test). | `reports/evidence/training_lineage/lineage_manifest.json` | Manifest Inspection | Đã xác minh | **CHO PHÉP** |
| **CLM-LINEAGE-03** | Kiến trúc YOLO11s, `imgsz=960`, `batch=6`, `optimizer=auto`, seed 0; lịch sử huấn luyện ghi nhận epoch 1–60 có dấu vết resume trước epoch 6. | `reports/evidence/training_lineage/args.yaml`, `results.csv` | Artifact Inspection | Đã xác minh | **CHO PHÉP** |
| **CLM-LINEAGE-04** | Checkpoint tiền huấn luyện ban đầu (Initial pretrained checkpoint) là `UNRESOLVED`; epoch trực tiếp sinh ra `best.pt` là `UNRESOLVED`. | `reports/evidence/training_lineage/lineage_manifest.json` | Manifest Inspection | Đã xác minh | **CHO PHÉP** |
| **CLM-LINEAGE-05** | Không phát hiện exact-hash hoặc filename collision giữa các split; chưa kiểm tra near-duplicate/session/subject leakage (không tuyên bố zero leakage). | `reports/evidence/training_lineage/lineage_manifest.json` | Audit Finding | Đã xác minh | **CHO PHÉP** |
| **CLM-LINEAGE-06** | MultiV và 11 video test mang vai trò `external_challenge_previously_seen` (không phải untouched holdout). | `reports/evidence/training_lineage/lineage_manifest.json` | Audit Finding | Đã xác minh | **CHO PHÉP** |

---

## 11. BẢNG TRẠNG THÁI SẴN SÀNG BÁO CÁO (REPORT READINESS MATRIX)

### 11.1. Ma trận Sẵn sàng Báo cáo KHKT Chuẩn hóa (9 Hạng mục)
| Hạng mục | Trạng thái |
| :--- | :--- |
| Kiến trúc / backend / database / UI runtime | `READY_VERIFIED_WITH_DEFINED_SCOPE` |
| Historical training setup | `READY_VERIFIED_WITH_CAVEATS` |
| Logic head-turning trong code | `READY_VERIFIED_WITH_DEFINED_SCOPE` |
| Cơ sở lý thuyết và bibliography | `DRAFTABLE_PENDING_CITATIONS` |
| Phone independent evaluation | `BLOCKED_D02` |
| Head-turning ground-truth evaluation | `BLOCKED_D03` |
| Tóm tắt (Abstract) | `DRAFTABLE_WITH_CAVEAT` |
| Kết luận (Conclusion) | `DRAFTABLE_WITH_CAVEAT` |
| Báo cáo Word cuối | `PENDING_PM_REVIEW` |

### 11.2. Danh mục 3 Khóa chặn Kỹ thuật Độc lập (Independent Blockers)
| Khóa chặn | Hạng mục Kỹ thuật | Trạng thái Hiện tại | Hướng Xử lý trong Báo cáo KHKT |
|---|---|---|---|
| **D-01** | Training Dataset Lineage cho YOLO Phone | **`CLOSED`** | Gói Pass 1.3 cung cấp đủ bằng chứng để tái dựng cấu hình huấn luyện lịch sử ở cấp artifact trong phạm vi được liệt kê; initial pretrained checkpoint và epoch sinh best.pt là UNRESOLVED. |
| **D-02** | Phone Independent Untouched Holdout Evaluation | **`OPEN`** | D-02 được định nghĩa là tập đánh giá độc lập, chưa từng tham gia train, validation, điều chỉnh threshold hoặc kiểm thử thủ công trước đó, đồng thời đại diện hợp lý cho bối cảnh sử dụng dự kiến. OOD evaluation là một đánh giá bổ sung, tách biệt với D-02. Chỉ báo cáo các chỉ số huấn luyện có nhãn `TRAINING_VALIDATION_ONLY`; không công bố chỉ số test độc lập giả định cho đến khi có dữ liệu holdout thực tế. |
| **D-03** | Head-Turning Ground-Truth Event Evaluation | **`OPEN`** | Không tuyên bố độ chính xác định lượng cho phát hiện quay đầu trong môi trường thực tế; chỉ trình bày giải thuật hình học kết hợp Temporal Guard ($\ge 1.25$s) và kết quả xác thực synthetic. |

---
**KẾT THÚC BỘ BẰNG CHỨNG KỸ THUẬT BÁO CÁO**
