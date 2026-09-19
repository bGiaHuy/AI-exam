# 📋 SỔ ĐĂNG KÝ KHIẾM KHUYẾT & KHOẢNG TRỐNG KỸ THUẬT (REPORT GAP REGISTER)
## DỰ ÁN: AI-POWERED AUTOMATED PROCTORING SYSTEM (AI EXAM CONTROL)
**Mã văn bản:** `REG-GAP-V3.1A`  
**Ngày cập nhật:** 14/09/2026 (Sprint 3.1A QA Corrections)  
**Mục đích:** Theo dõi, phân loại mức độ nghiêm trọng và thiết lập điều kiện đóng cho toàn bộ các điểm sai lệch, khoảng trống dữ liệu hoặc thành phần tồn dư giữa thực tế mã nguồn và mục tiêu hoàn thiện Báo cáo KHKT.

---

## 1. BẢNG TỔNG HỢP DANH MỤC GAPS

| Mã Gap | Tên khiếm khuyết | Mức độ nghiêm trọng | Loại yêu cầu | Trạng thái kỹ thuật | Ghi chú xử lý |
|---|---|---|---|---|---|
| **GAP-D01** | Training Dataset Lineage cho YOLO Phone | **BLOCKER (CAO)** | Cần Dữ liệu (Data) | **`CLOSED`** | Đã nhập và kiểm chứng toàn vẹn gói bàn giao Pass 1.3 tại `reports/evidence/training_lineage/` |
| **GAP-D02** | Phone Independent Untouched Holdout Evaluation | **BLOCKER (CAO)** | Cần Dữ liệu (Data) | **`OPEN`** | Chưa có tập holdout test độc lập ngoài quá trình train |
| **GAP-D03** | Head-Turning Ground-Truth Event Evaluation | **BLOCKER (CAO)** | Cần Dữ liệu (Data) | **`OPEN`** | Chưa có tập video thực tế gán nhãn mốc thời gian vi phạm chuẩn |
| **GAP-FE-01** | Lệch Interface TypeScript `WebSocketDetectionPayload` | **MEDIUM (TRUNG BÌNH)** | Sửa Code (Frontend) | **`CLOSED`** | Đã căn chỉnh 8 telemetry fields, `tsc --noEmit` exit 0 |
| **GAP-LEG-01** | Tồn dư Tệp Tĩnh Mockup và Avatar Lịch sử trong `public/` | **LOW (THẤP)** | Dọn dẹp Tài nguyên | **`CLOSED`** | Đã xóa 12 files `screens/` và 8 files `avatars/`; URL cũ phân giải về generic SPA fallback |
| **GAP-LEG-02** | Tồn dư Tệp Mã nguồn Độc lập Cũ (`api_server.py`, `test_demo.py`) | **LOW (THẤP)** | Dọn dẹp Mã nguồn | **`CLOSED`** | Phân loại `ARCHIVED_NON_RUNTIME`, di chuyển vào `archive/legacy/` |
| **GAP-DOC-01** | Tệp `index.html` còn liên kết CDN Google Fonts | **LOW (THẤP)** | Cấu hình Offline | **`CLOSED`** | Đã gỡ bỏ toàn bộ liên kết Google Fonts CDN |
| **GAP-DOC-02** | Thẻ meta `index.html` còn nhắc đến ma trận phòng thi, lập biên bản | **LOW (THẤP)** | Sửa Tài liệu / HTML | **`CLOSED`** | Đã cập nhật description đúng phạm vi đóng băng |
| **GAP-API-01** | Endpoint `/api/clips/{filename}` legacy | **LOW (THẤP)** | Tối ưu API Router | **`CLOSED`** | Đã đưa sau cờ `ENABLE_LEGACY_CLIPS=false` (mặc định tắt, 404, ẩn khỏi OpenAPI) |
| **GAP-API-02** | Endpoint `POST /api/detect/frame` deprecated | **LOW (THẤP)** | Tối ưu API Router | **`CLOSED`** | Đã vô hiệu hóa mặc định sau cờ `ENABLE_DEPRECATED_INGEST=false` |
| **GAP-TOOL-01**| Frontend linting chưa được cấu hình độc lập | **LOW (THẤP)** | Công cụ kiểm thử (Tooling) | **`NOT_CONFIGURED`** | Script `lint` hiện chỉ là alias gọi `tsc --noEmit`; chưa có ESLint/Biome |
| **GAP-SEM-01** | Mơ hồ trong chuẩn hóa confidence cho giá trị số nhỏ | **LOW (THẤP)** | Rủi ro Ngữ nghĩa (Semantics) | **`OPEN`** | Giá trị lỗi như `2.0` có thể bị hiểu là 2% (0.02) do tầng tương thích ngược |

---

## 2. CHI TIẾT TỪNG KHIẾM KHUYẾT KỸ THUẬT

### GAP-D01: Training Dataset Lineage cho YOLO Phone
- **Mã Gap:** `GAP-D01` (Kế thừa Khóa chặn `D-01`)
- **Mức độ nghiêm trọng:** **BLOCKER (Đã khắc phục)**
- **Mô tả chi tiết:**
  Gói Pass 1.3 cung cấp đủ bằng chứng để tái dựng cấu hình huấn luyện lịch sử ở cấp artifact trong phạm vi được liệt kê.
- **Trạng thái:** **`CLOSED`** (14/09/2026 - Sprint 3.2A).
  - Đã nhập khẩu đúng 10 tệp canonical Pass 1.3 vào `reports/evidence/training_lineage/`.
  - Bộ kiểm chứng `scripts/verify_training_lineage_handoff.py` xác minh toàn bộ mã băm SHA-256, dung lượng và các xác nhận kỹ thuật bắt buộc đạt 100%.
  - Các thông số kỹ thuật được phép đưa vào Báo cáo KHKT:
    1. Tệp trọng số triển khai `phone_detector_v5.pt` có cùng SHA-256 (`23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2`, kích thước 19.245.082 bytes) với artifact `best.pt` được xác định trong run `phone_detector_v5` (đối chiếu đồng nhất artifact bằng SHA-256).
    2. Dataset lịch sử `phone_merged` gồm 2.961 ảnh và 3.706 phone boxes (train: 2.434, val: 382, test nội bộ: 145).
    3. Kiến trúc `YOLO11s`, `imgsz=960`, `batch=6`, `optimizer=auto`, seed 0.
    4. Lịch sử huấn luyện ghi nhận epoch 1–60, có dấu vết resume trước epoch 6.
    5. Các metric trong `results.csv` là `TRAINING_VALIDATION_ONLY`.
    6. Initial pretrained checkpoint: `UNRESOLVED` (không khẳng định chắc chắn từ `yolo11s.pt`).
    7. Epoch trực tiếp sinh ra `best.pt`: `UNRESOLVED` (không khẳng định epoch 55 là best epoch).
    8. Không phát hiện exact-hash hoặc filename collision giữa các split; chưa kiểm tra near-duplicate/session/subject leakage.
    9. MultiV và 11 video test mang vai trò `external_challenge_previously_seen`.

---

### GAP-D02: Phone Independent Untouched Holdout Evaluation
- **Mã Gap:** `GAP-D02` (Khóa chặn `D-02`)
- **Mức độ nghiêm trọng:** **BLOCKER (Nghiêm trọng đối với Báo cáo Model)**
- **Mô tả chi tiết:**
  D-02 được định nghĩa là tập đánh giá độc lập, chưa từng tham gia train, validation, điều chỉnh threshold hoặc kiểm thử thủ công trước đó, đồng thời đại diện hợp lý cho bối cảnh sử dụng dự kiến. OOD evaluation là một đánh giá bổ sung, tách biệt với D-02.
- **Trạng thái:** **`OPEN`** (Trong Báo cáo KHKT: chỉ báo cáo các chỉ số huấn luyện có nhãn `TRAINING_VALIDATION_ONLY`; không công bố chỉ số test độc lập giả định).

---

### GAP-D03: Head-Turning Ground-Truth Event Evaluation
- **Mã Gap:** `GAP-D03` (Khóa chặn `D-03`)
- **Mức độ nghiêm trọng:** **BLOCKER (Nghiêm trọng đối với Báo cáo Phân tích Tư thế)**
- **Mô tả chi tiết:**
  Hệ thống phát hiện quay đầu dựa trên ước lượng tư thế 17 điểm COCO (`yolo11m-pose.pt`) kết hợp thuật toán hình học khuôn mặt và bộ đếm thời gian liên tục (`posture_alert_seconds >= 1.25s`). Mặc dù logic thời gian đã vượt qua các bài unit test synthetic trong `backend.tests.test_refactored_system`, hiện chưa có tập video phòng thi thực tế được gán nhãn chuẩn theo mốc thời gian vi phạm (onset/offset ground truth intervals) để benchmark định lượng (tIoU, Event F1-score, Onset Error).
- **Trạng thái:** **`OPEN`** (Trong Báo cáo KHKT: chỉ trình bày thiết kế thuật toán và kiểm thử synthetic; không công bố số liệu định lượng giả định).

---

### GAP-FE-01: Lệch Interface TypeScript `WebSocketDetectionPayload` gây lỗi `tsc --noEmit`
- **Mã Gap:** `GAP-FE-01`
- **Mức độ nghiêm trọng:** **MEDIUM (Đã giải quyết)**
- **Mô tả và Nguyên nhân:**
  Interface `WebSocketDetectionPayload` trong `src/services/aiModelService.ts` và `src/types.ts` thiếu 5 trường telemetry mà backend trả về (`server_packets_received`, `server_frames_decoded`, `inference_processed_frames`, `inference_pending_frames`, `result_messages_sent`), gây ra 14 lỗi TS2339 khi chạy `npx tsc --noEmit`.
- **Hành động khắc phục trong Sprint 3.1:**
  1. Bổ sung đầy đủ định nghĩa kiểu dữ liệu và JSDoc cho 5 trường telemetry trên, cộng thêm 3 trường liên quan (`first_decoded_monotonic`, `last_decoded_monotonic`, `effective_acquisition_fps`).
  2. Tạo bộ test tự động `src/services/__tests__/test_telemetry_contract.ts` kiểm chứng toàn diện tính toàn vẹn khi phân giải payload.
  3. Kiểm chứng `npx tsc --noEmit` trả về exit code 0 không có lỗi.
- **Trạng thái:** **`CLOSED`** (14/09/2026).

---

### GAP-LEG-01: Tồn dư Tệp Tĩnh Mockup và Avatar Lịch sử trong thư mục `public/`
- **Mã Gap:** `GAP-LEG-01`
- **Mức độ nghiêm trọng:** **LOW (Đã giải quyết)**
- **Mô tả và Phân loại:**
  12 tệp HTML tĩnh trong `public/screens/` và 8 tệp ảnh trong `public/avatars/` không được code React sử dụng nhưng vẫn có thể bị truy cập trực tiếp qua URL (phân loại `REACHABLE_BUT_UNUSED`).
- **Hành động khắc phục và Kết quả xác minh thực tế:**
  1. Xóa hoàn toàn 12 file trong `public/screens/` và 8 file trong `public/avatars/`.
  2. Xác minh `npm run build`: bundle `dist/` không còn bất kỳ thư mục `screens/` hay `avatars/` nào.
  3. Kiểm tra HTTP request thực tế qua `scripts/verify_legacy_assets.py`:
     - Yêu cầu tới các URL cũ (ví dụ `/screens/04-report-protocol.html` hay `/avatars/student_01.jpg`) được dev server phân giải chính xác:
       `Legacy asset removed; request resolves to generic SPA fallback, not legacy content.`
     - Trả về HTTP 200 dạng text/html của `index.html` tổng quát, không chứa nội dung biên bản/ma trận phòng thi, và không trả MIME bytes ảnh JPEG cũ.
- **Trạng thái:** **`CLOSED`** (14/09/2026).

---

### GAP-LEG-02: Tồn dư Tệp Mã nguồn Độc lập Cũ
- **Mã Gap:** `GAP-LEG-02`
- **Mức độ nghiêm trọng:** **LOW (Đã giải quyết)**
- **Phân loại kỹ thuật:** **`ARCHIVED_NON_RUNTIME`**
- **Mô tả và Hành động khắc phục:**
  1. Tạo thư mục `archive/legacy/`.
  2. Di chuyển `model/api_server.py` (chứa mock endpoint trợ lý quy chế và session RAM cũ) và `model/test_demo.py` (script cv2.imshow cũ) vào `archive/legacy/`.
  3. Xác minh tính cô lập:
     - Không được import bởi bất kỳ file nào trong `backend/` hay `src/`.
     - Không được đóng gói vào frontend bundle.
     - Không được gọi bởi backend entrypoint.
  4. Cập nhật `model/README.md` khẳng định entrypoint backend chính thức duy nhất là `backend.main:app`.
- **Trạng thái:** **`CLOSED`** (14/09/2026).

---

### GAP-DOC-01: Tệp `index.html` còn liên kết CDN Google Fonts
- **Mã Gap:** `GAP-DOC-01`
- **Mức độ nghiêm trọng:** **LOW (Đã giải quyết)**
- **Hành động khắc phục:**
  Gỡ bỏ toàn bộ các thẻ `<link rel="preconnect" href="https://fonts.googleapis.com">` và link CSS gọi phông chữ từ CDN ngoài khỏi `index.html`. Hệ thống sử dụng ngăn xếp phông chữ hệ thống tiêu chuẩn (`system-ui, -apple-system, sans-serif, monospace`), tuân thủ 100% nguyên tắc Offline-First.
- **Trạng thái:** **`CLOSED`** (14/09/2026).

---

### GAP-DOC-02: Thẻ meta `index.html` còn nhắc đến ma trận phòng thi, lập biên bản
- **Mã Gap:** `GAP-DOC-02`
- **Mức độ nghiêm trọng:** **LOW (Đã giải quyết)**
- **Hành động khắc phục:**
  Cập nhật thẻ `<title>` thành `AI Exam Control - Hệ thống Giám sát Phòng thi Thị giác Máy tính` và thẻ `<meta name="description">` thành mô tả chuẩn hóa theo phạm vi đóng băng: nhận diện điện thoại, phát hiện quay đầu, trích xuất clip bằng chứng 15s tự động, vận hành offline trên máy trạm cục bộ.
- **Trạng thái:** **`CLOSED`** (14/09/2026).

---

### GAP-API-01: Endpoint `GET /api/clips/{filename}` legacy
- **Mã Gap:** `GAP-API-01`
- **Mức độ nghiêm trọng:** **LOW (Đã giải quyết)**
- **Hành động khắc phục:**
  1. Thống nhất `/evidence/{filename}` là canonical static route phục vụ video và ảnh bằng chứng.
  2. Tách route cũ `/api/clips/{filename}` vào `legacy_clips_router` và bảo vệ sau cờ môi trường `ENABLE_LEGACY_CLIPS=false` (mặc định tắt trong môi trường sản xuất).
  3. Khi tắt cờ (mặc định), gọi `/api/clips/{filename}` trả về HTTP 404 và endpoint ẩn khỏi `/openapi.json`.
  4. Khi bật cờ, endpoint trả về header cảnh báo `X-API-Deprecation` và áp dụng `os.path.basename` để phòng vệ chống path traversal.
  5. Đã bổ sung kiểm thử tự động toàn diện trong `test_31`.
- **Trạng thái:** **`CLOSED`** (14/09/2026).

---

### GAP-API-02: Endpoint `POST /api/detect/frame` đã deprecated nhưng vẫn mở tại router
- **Mã Gap:** `GAP-API-02`
- **Mức độ nghiêm trọng:** **LOW (Đã giải quyết)**
- **Hành động khắc phục:**
  1. Tách endpoint kiểm thử `POST /api/test/trigger_incident` vào router riêng, bảo vệ bằng biến môi trường `ENABLE_TEST_ENDPOINTS` (mặc định `False`).
  2. Tách endpoint ingest Base64 cũ `POST /api/detect/frame` vào router riêng, bảo vệ bằng biến môi trường `ENABLE_DEPRECATED_INGEST` (mặc định `False`).
  3. Trong chế độ sản xuất mặc định, cả 2 endpoint đều trả về 404 và không xuất hiện trong tài liệu OpenAPI `/openapi.json`.
  4. Bổ sung bài kiểm thử `test_29_test_endpoint_guard_and_deprecated_ingest_guard` xác minh các điều kiện này.
- **Trạng thái:** **`CLOSED`** (14/09/2026).

---

### GAP-TOOL-01: Frontend linting chưa được cấu hình độc lập
- **Mã Gap:** `GAP-TOOL-01`
- **Mức độ nghiêm trọng:** **LOW (Thấp - Công cụ kiểm thử)**
- **Mô tả chi tiết:**
  Trong `package.json`, script `"lint"` được gán lệnh `"tsc --noEmit"`. Mặc dù `tsc` kiểm tra kiểu dữ liệu tĩnh nghiêm ngặt, dự án chưa cấu hình một công cụ linter tĩnh AST riêng biệt (như ESLint, Oxlint, Biome) để bắt các lỗi style hay quy chuẩn React hooks. Lệnh `npm run lint` thực chất chỉ là kiểm tra biên dịch TypeScript.
- **Ràng buộc:** Không tự ý cài đặt thêm cả bộ công cụ ESLint trong correction pass ngắn này; ghi nhận trung thực trạng thái.
- **Trạng thái:** **`NOT_CONFIGURED`** (Ghi nhận công cụ chưa cấu hình; không coi tsc là linter).

---

### GAP-SEM-01: Mơ hồ trong chuẩn hóa confidence cho giá trị số nhỏ
- **Mã Gap:** `GAP-SEM-01`
- **Mức độ nghiêm trọng:** **LOW (Thấp - Rủi ro Ngữ nghĩa Dữ liệu)**
- **Mô tả chi tiết:**
  Trình xác thực `normalize_confidence` trong `backend/schemas.py` quy định: giá trị $> 1.0$ và $\le 100.0$ được coi là dữ liệu legacy (dạng phần trăm cũ như 90.0, 93.5) và tự động chia 100 để đưa về xác suất `[0.0, 1.0]`.
- **Rủi ro còn lại (Residual Risk):**
  Nếu một client gửi nhầm giá trị xác suất lỗi như `2.0` (thực tế có thể là lỗi ngoài đoạn $[0, 1]$), validator sẽ hiểu là 2% và tự động chuẩn hóa thành `0.02` thay vì từ chối dữ liệu. Do cấu trúc CSDL hiện tại không có cột phân biệt phiên bản bản ghi (legacy format vs canonical format), hiện tượng này là sự thỏa hiệp có chủ ý để duy trì tính tương thích ngược.
- **Điều kiện đóng Gap:** Thực hiện migration dữ liệu SQLite cũ để chuẩn hóa toàn bộ bản ghi sang xác suất `[0.0, 1.0]`, sau đó khóa chặt schema chỉ chấp nhận đoạn $[0.0, 1.0]$ thuần túy (từ chối mọi giá trị $> 1.0$).
- **Trạng thái:** **`OPEN`** (Ghi nhận rủi ro còn lại trong báo cáo KHKT).

---
**KẾT THÚC SỔ ĐĂNG KÝ KHIẾM KHUYẾT & KHOẢNG TRỐNG KỸ THUẬT**
