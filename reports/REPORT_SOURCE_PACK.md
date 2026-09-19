# 📦 NGUỒN TÀI LIỆU DỰ ÁN CHO BÁO CÁO KHOA HỌC KỸ THUẬT (REPORT SOURCE PACK)
## DỰ ÁN: AI-POWERED AUTOMATED PROCTORING SYSTEM (AI EXAM CONTROL)
**Mã tài liệu:** `RPT-SRC-V4.0`  
**Ngày phát hành:** 14/09/2026 (Sprint 4.0A — Corrected Evidence-Grounded Edition)  
**Mục đích:** Cung cấp nguồn thông tin kỹ thuật, số liệu thực nghiệm và bằng chứng mã nguồn đã được đối soát chi tiết qua các bài kiểm thử và rà soát mã nguồn để phục vụ viết Báo cáo Nghiên cứu Khoa học Kỹ thuật (KHKT). Tài liệu này **không phải tài liệu quảng bá sản phẩm**, mà là bản đối chiếu khoa học có căn cứ thực nghiệm nghiêm ngặt.

---

## A. TÊN ĐỀ TÀI TẠM THỜI (PROPOSED PROJECT TITLES)

1. **Tên đề tài 1 (Đề xuất ưu tiên):**  
   *Hệ thống Thị giác Máy tính Giám sát Phòng thi: Phát hiện Hành vi Sử dụng Điện thoại, Tư thế Quay đầu và Tự động Trích xuất Video Bằng chứng trên Máy trạm Cục bộ.*  
   - **Lý do khuyến nghị:** Phản ánh chính xác phạm vi kỹ thuật thực tế của hệ thống: phát hiện điện thoại, phát hiện quay đầu, trích xuất clip bằng chứng ~15 giây, runtime được thiết kế để xử lý cục bộ trên máy trạm của giám thị, không có các tính năng nhận diện danh tính hay xử lý kỷ luật tự động.

2. **Tên đề tài 2:**  
   *Nghiên cứu Ứng dụng Thị giác Máy tính và Heuristic Không-Thời gian trong Hỗ trợ Giám thị Phòng thi: Phát hiện Thiết bị Di động và Hành vi Trao đổi Bài thi.*

3. **Tên đề tài 3:**  
   *Hệ thống Giám sát Hỗ trợ Giám thị Phát hiện Dấu hiệu Gian lận Phòng thi Bằng Computer Vision và Bộ đệm Video Bằng chứng Hai Pipeline.*

---

## B. BÀI TOÁN VÀ PHẠM VI NGHIÊN CỨU (PROBLEM & SCOPE)

### 1. Vấn đề Cần Giải quyết
Trong các kỳ thi trực tiếp trên giấy (in-person paper exams), một giám thị thường phải bao quát phòng thi từ 24 đến 40 thí sinh. Khả năng quan sát của con người chịu nhiều giới hạn:
- **Hiện tượng mù quan sát (Inattentional Blindness) và mỏi mắt:** Giám thị không thể quan sát liên tục mọi vị trí cùng một lúc trong ca thi kéo dài 90–180 phút.
- **Hành vi vi phạm diễn ra chớp nhoáng:** Thí sinh giấu điện thoại dưới hộc bàn hoặc quay đầu nhìn bài thí sinh bên cạnh trong khoảng thời gian rất ngắn (1–2 giây) khi giám thị nhìn hướng khác.
- **Thiếu dữ liệu video ghi nhận thời gian thực để đối soát:** Khi giám thị phát hiện bằng mắt thường nhưng không có ghi hình lại mốc thời gian vi phạm, việc xử lý vi phạm dễ dẫn đến tranh cãi, khiếu nại hoặc khó khăn trong khâu thẩm định của Hội đồng thi.

### 2. Đối tượng Sử dụng và Vai trò
- **Đối tượng sử dụng trực tiếp:** Giám thị phòng thi (Proctor) tại bàn làm việc giám sát.
- **Mô hình phối hợp Người - Máy (Human-in-the-Loop):** Hệ thống đóng vai trò công cụ trợ lý phát hiện và cảnh báo sớm. Hệ thống **không đưa ra quyết định kỷ luật tự động**, không đình chỉ thi tự động. Quyền quyết định xác nhận vi phạm (`confirmed`) hoặc bỏ qua (`dismissed`) thuộc về phán đoán nghiệp vụ của giám thị con người.

### 3. Đầu vào, Xử lý và Đầu ra
- **Đầu vào (Input):** Luồng video 1 camera (webcam giám sát góc nhìn bao quát phòng thi hoặc tệp video mô phỏng phòng thi) được truyền từ trình duyệt qua giao thức WebSocket nhị phân (gói tin gồm 16-byte header + dữ liệu ảnh JPEG).
- **Xử lý (Processing):** Kiến trúc hai pipeline bất đồng bộ:
  - *Pipeline 1 (Thu nhận & Lưu đệm):* Bộ đệm vòng tròn `RingBuffer` (dung lượng mặc định 150 slot) thu nhận 15 FPS liên tục, tách biệt với pipeline suy luận AI.
  - *Pipeline 2 (Suy luận AI mới nhất):* Hàng đợi `SingleSlotInferenceBuffer` (độ sâu backlog $\le 1$) nạp frame mới nhất vào mô hình YOLO11s phát hiện điện thoại và YOLO11m-Pose ước lượng điểm mốc tư thế kết hợp giải thuật điểm nghi vấn tư thế đầu từ hình học keypoint COCO và bộ đếm thời gian liên tục (`Temporal Continuity Guard` $\ge 1.25$s).
- **Đầu ra (Output):**
  - Khung chữ nhật (bounding box) và khung xương tư thế hiển thị trực tiếp trên giao diện giám thị.
  - Mức độ cảnh báo: Cờ Vàng (cảnh báo quan sát) và Cờ Đỏ (kích hoạt sự cố).
  - Bản ghi sự cố ẩn danh lưu vào cơ sở dữ liệu SQLite (`cheating_system.db`).
  - Video clip bằng chứng MP4 độ dài khoảng 15 giây (~5 giây trước và ~10 giây sau sự cố).
  - Modal phát video bằng chứng cho phép giám thị xem lại và chọn Xác nhận / Bỏ qua.

### 4. Các Chức năng Nằm Ngoài Phạm vi (Out-of-Scope)
Hệ thống **không chứa các tính năng ngoài phạm vi**:
- Không nhận diện danh tính thí sinh (không có Tên, Số báo danh, CCCD).
- Không nhận diện khuôn mặt (không dùng FaceNet, không trích xuất/lưu trữ vector sinh trắc học).
- Không sử dụng mô hình ngôn ngữ lớn (LLM), RAG hay chatbot tra cứu quy chế.
- Không tự động lập biên bản vi phạm thi, không sinh văn bản biên bản, không có chữ ký số.
- Không quản lý ma trận nhiều phòng thi tập trung qua máy chủ đám mây.

---

## C. KIẾN TRÚC HỆ THỐNG THỰC TẾ (SYSTEM ARCHITECTURE)

Hệ thống được thiết kế theo mô hình Offline-First, runtime hiện tại được thiết kế để xử lý cục bộ và không có phụ thuộc cloud được xác định trong luồng chính (localhost).

```
[Camera / Trình duyệt] 
       │ (15 FPS, Binary WebSocket: 16-byte header + JPEG)
       ▼
[FastAPI Ingest Router] ─── backend/routers/ai_engine.py
       ├──► [Pipeline 1: Lossless RingBuffer (150 frames, ~10s)] ─── backend/services/ring_buffer.py
       │           │
       │           └───► (Khi có Cờ Đỏ) ──► [Trích xuất MP4 ~15s] ──► ./data/evidence/inc_*.mp4
       │
       └──► [Pipeline 2: SingleSlotInferenceBuffer (Depth <= 1)] ─── backend/services/inference_worker.py
                   │
                   ▼ (Tự động drop frame cũ, chống trễ tích lũy)
       [ExamBehaviorDetector Engine] ─── model/exam_analyzer.py
          ├── YOLO11s Phone Detector (phone_detector_v5.pt) ──► BBox {phone}
          ├── YOLO11m-Pose (yolo11m-pose.pt) ───────────────► 17 Landmarks + KeypointSmoother
          ├── Keypoint Geometric Posture Suspicion ─────────► Posture Suspicion Score [0.0 - 1.0]
          └── Temporal Continuity Guard (>= 1.25s) ─────────► Incident Escalation (RED FLAG)
                   │
                   ▼ (Đẩy sự cố vào hàng đợi luồng an toàn)
       [DBWriteQueue] ─── backend/services/db_queue.py
                   │
                   ▼ (Giao dịch tuần tự, WAL mode)
       [SQLite 3 Engine: ./cheating_system.db] ─── backend/database.py, backend/models.py
                   │
                   ▼
       [FastAPI REST API & Canonical Static Evidence Mount /evidence] ─── backend/main.py
                   ▲
                   │ (Polling 2.0s danh sách sự cố & Modal phát clip MP4)
       [Streamlined Proctor Dashboard (React 19)] ─── src/components/StreamlinedProctorDashboard.tsx
```

### Chi tiết Các Thành phần và Căn cứ Mã nguồn / Bằng chứng:
1. **Nguồn Video & Ingestion Trình duyệt:** `src/components/StreamlinedProctorDashboard.tsx` thu nhận webcam thiết bị qua `navigator.mediaDevices.getUserMedia` hoặc tệp video nội bộ, mã hóa JPEG chất lượng 0.7 và đóng gói header nhị phân 16 byte gửi qua WebSocket. (Căn cứ: `CLM-PIPE-01`, `test_26`).
2. **Bộ Nhận WebSocket Backend:** `backend/routers/ai_engine.py:websocket_endpoint` unpack header nhị phân, kiểm tra số thứ tự gói tin và mốc thời gian monotonic máy chủ, phân phối frame sang hai pipeline độc lập. (Căn cứ: `CLM-TELE-01`, `test_26`, `test_27`).
3. **Pipeline 1 - Bộ đệm Video RingBuffer:** `backend/services/ring_buffer.py` duy trì hàng đợi vòng 150 slot bộ nhớ. Khi có tín hiệu kích hoạt sự cố, RingBuffer thu thập đủ 10 giây post-roll, áp dụng giải thuật nội suy lại trên lưới thời gian (time-grid resampling) để phát sinh tệp MP4 có tốc độ phát 1.0x tự nhiên. (Căn cứ: `CLM-CLIP-01`, `CLM-CLIP-02`, `CLM-CLIP-03`, `test_06`, `test_08`, `test_13`).
4. **Pipeline 2 - Hàng đợi Suy luận Single-Slot:** `backend/services/inference_worker.py:SingleSlotInferenceBuffer` duy trì độ sâu hàng đợi $\le 1$. Nếu AI đang bận suy luận, các frame trung gian mới tới sẽ tự động ghi đè frame chờ cũ, ngăn ngừa hiện tượng trễ tích lũy hàng đợi (queue backlog lag). (Căn cứ: `CLM-PIPE-02`, `test_28`).
5. **Mô hình Nhận diện Điện thoại:** `model/exam_analyzer.py` gọi trọng số `model/weights/phone_detector_v5.pt`, trả về bounding box và độ tin cậy. (Căn cứ: `CLM-MODEL-01`, `CLM-LINEAGE-01`).
6. **Mô hình Ước lượng Tư thế & Heuristic:** `model/exam_analyzer.py` gọi `model/weights/yolo11m-pose.pt`, trích xuất 17 điểm mốc COCO, tính toán tỷ lệ hình học mặt và áp dụng bộ làm mượt `KeypointSmoother` (EMA $\alpha=0.75$). (Căn cứ: `CLM-MODEL-02`).
7. **Bộ Bảo vệ Tính Liên tục Thời gian (Temporal Continuity Guard):** `backend/services/inference_worker.py:IncidentManager` đếm thời gian vi phạm tích lũy liên tục theo mốc thời gian thực của frame. Chỉ khi thời gian duy trì tư thế nghi vấn $\ge 1.25$ giây mới kích hoạt Cờ Đỏ. (Căn cứ: `CLM-PIPE-02`, `test_02`, `test_26`).
8. **Hàng đợi Ghi CSDL An toàn Luồng (DBWriteQueue):** `backend/services/db_queue.py` nhận yêu cầu ghi sự cố từ luồng suy luận AI và ghi tuần tự vào SQLite thông qua một worker duy nhất, ngăn ngừa lỗi khóa CSDL trong các trường hợp đã kiểm thử. (Căn cứ: `CLM-DB-02`, `test_15`, `test_24`).
9. **Cơ sở Dữ liệu SQLite 3:** Tệp `./cheating_system.db`, kết nối được cấu hình bật chế độ WAL (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) và bật ràng buộc khóa ngoại. Bảng `incidents` lưu trữ ẩn danh bằng `track_id`. (Căn cứ: `CLM-ARCH-02`, `CLM-DB-01`, `test_23`).
10. **Giao thức REST API & Phục vụ Tệp Tĩnh Canonical:** `backend/main.py` phục vụ API RESTful (`/api/incidents`, `/api/settings/ai`, `/api/session/telemetry`) và gắn static mount độc quyền `/evidence/{filename}` trỏ tới `./data/evidence/`. (Căn cứ: `CLM-SEC-01`, `CLM-GUARD-01`, `test_31`).
11. **Giao diện Giám thị (UI):** Ứng dụng React 19 chạy trên trình duyệt, kết nối API qua tầng dịch vụ tập trung `src/services/api.ts`. (Căn cứ: `CLM-FE-01`, `CLM-FE-02`, `CLM-FE-03`).

---

## D. CƠ SỞ MÔ HÌNH PHÁT HIỆN ĐIỆN THOẠI (YOLO PHONE DETECTOR LINEAGE)

Dữ liệu nguồn gốc mô hình được trích xuất trực tiếp từ gói bằng chứng Pass 1.3 tại `reports/evidence/training_lineage/`:

### 1. Thông số Kiến trúc & Siêu Tham số Huấn luyện Lịch sử
- **Kiến trúc mô hình:** `YOLO11s` (phiên bản kích thước nhỏ của họ YOLO11).
- **Phân loại lớp:** 1 lớp duy nhất: `{0: 'phone'}`.
- **Tập dữ liệu lịch sử:** `phone_merged` gồm tổng cộng **2.961 ảnh** và **3.706 bounding boxes**.
- **Phân bố các tập:**
  - *Tập Huấn luyện (Train):* 2.434 ảnh (3.042 phone boxes).
  - *Tập Kiểm định (Validation):* 382 ảnh (490 phone boxes).
  - *Tập Kiểm thử Nội bộ (Internal Test):* 145 ảnh (174 phone boxes).
- **Nguồn gốc dữ liệu nguồn:** Tương ứng theo tên tệp, số lượng mẫu và cấu trúc phân chia từ 3 gói dự án Roboflow mở thuộc tác giả `du-tran` theo giấy phép CC BY 4.0:
  1. `mobilephone` (v3, xuất 26/08/2026): 963 ảnh (train: 823, val: 100, test: 40).
  2. `mobilephone2` (v1, xuất 26/08/2026): 1.000 ảnh (train: 801, val: 175, test: 24).
  3. `mobilephone3` (v1, xuất 26/08/2026): 998 ảnh (train: 810, val: 107, test: 81).
- **Siêu tham số huấn luyện của run cuối (trích từ `args.yaml`):**
  - Kích thước ảnh đầu vào (`imgsz`): $960 \times 960$ pixel.
  - Kích thước lô (`batch`): 6.
  - Trình tối ưu hóa (`optimizer`): `auto` (SGD / AdamW theo heuristic của Ultralytics).
  - Hạt giống ngẫu nhiên (`seed`): 0, cờ tất định `deterministic: True`.
  - Đóng kỹ thuật Mosaic (`close_mosaic`): 10 epoch cuối.
- **Dấu vết tiếp tục huấn luyện (Training Resume Footprint):**
  - Tệp cấu hình `args.yaml` ghi nhận tham số `model` và `resume` đều trỏ vào `last.pt`.
  - Nhật ký `results.csv` ghi nhận 60 epoch; cột thời gian `time` tích lũy đạt 1.219,98 giây tại Epoch 5 và đột ngột reset về 119,816 giây tại Epoch 6.
  - *Kết luận khoa học:* Quá trình huấn luyện đã được phục hồi (resume) ít nhất một lần trước epoch 6 (`resume_boundary_observed_before_epoch = 6`).
- **Mã băm SHA-256 đối chiếu trọng số:**
  - Tệp trọng số triển khai `phone_detector_v5.pt` (19.245.082 byte):  
    `23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2`
  - Tệp trọng số artifact `best.pt` của run huấn luyện:  
    `23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2`
  - *Kết luận:* Tệp trọng số triển khai có cùng mã băm SHA-256 với artifact `best.pt` được xác định trong run huấn luyện.

### 2. Các Giới hạn và Caveat Bắt buộc Phải Ghi Rõ trong Báo cáo:
1. **Bản chất metric:** Mọi chỉ số đánh giá ghi nhận trong `results.csv` (ví dụ: mAP50 cao nhất 78,58% tại epoch 55; mAP50 epoch 60 là 76,92%) đều mang bản chất **`TRAINING_VALIDATION_ONLY`**. Tuyệt đối không được dùng các chỉ số này để tuyên bố hiệu năng thực tế ngoài đời.
2. **Checkpoint tiền huấn luyện ban đầu:** Trạng thái **`UNRESOLVED`** (do không lưu giữ log/config của lần chạy từ epoch 1–5 nên không khẳng định tuyệt đối là khởi tạo từ `yolo11s.pt`).
3. **Epoch sinh ra `best.pt`:** Trạng thái **`UNRESOLVED`** (do thuật toán chọn best model của Ultralytics phụ thuộc fitness score tổng hợp, không có căn cứ khẳng định epoch 55 là epoch sinh ra trọng số cuối cùng).
4. **Kiểm tra rò rỉ (Data Leakage):** Kiểm tra mã băm nội dung SHA-256 và tên tệp giữa train, valid và test cho thấy 0 trường hợp trùng lặp (collision). Tuy nhiên, **chưa thực hiện kiểm tra độ tương đồng ảnh gần giống (perceptual hash) và chưa kiểm tra rò rỉ cấp phiên/thí sinh (session/subject correlation)**. Do đó, nghiêm cấm tuyên bố "zero leakage tuyệt đối".
5. **Tập dữ liệu kiểm thử MultiV (11 video test):** Mang vai trò **`external_challenge_previously_seen`**, không đạt tiêu chuẩn tập kiểm thử độc lập (untouched holdout).
6. **Khóa chặn D-02:** Tiếp tục duy trì trạng thái **`OPEN`**.

---

## E. PHƯƠNG PHÁP PHÁT HIỆN QUAY ĐẦU NHÌN BÀI (HEAD-TURNING SUSPICION ESTIMATION)

### 1. Cơ sở Thuật toán và Tín hiệu Hình học Điểm Mốc
Hệ thống không sử dụng mô hình phân loại hành vi hộp đen (black-box video action classification) và không đo góc quay vật lý 3D trong không gian, mà tính toán điểm nghi vấn tư thế đầu được chuẩn hóa từ quan hệ hình học giữa các keypoint COCO theo thời gian thực:
- **Điểm mốc đầu vào:** 17 điểm mốc COCO từ `yolo11m-pose.pt`. Các điểm mốc trọng yếu phục vụ tính toán gồm:
  - Điểm mũi: `Nose` (Keypoint index 0)
  - Mắt trái, Mắt phải: `Left Eye` (idx 1), `Right Eye` (idx 2)
  - Tai trái, Tai phải: `Left Ear` (idx 3), `Right Ear` (idx 4)
  - Vai trái, Vai phải: `Left Shoulder` (idx 5), `Right Shoulder` (idx 6)
- **Hình học Chiếu Điểm Mốc Đầu (Head Keypoints Projective Geometry):**  
  - Vector nối hai mắt $\vec{v}_{\text{eyes}} = (x_{\text{re}} - x_{\text{le}}, y_{\text{re}} - y_{\text{le}})$, khoảng cách hai mắt $d_{\text{eye}} = \|\vec{v}_{\text{eyes}}\|$.
  - Trung điểm hai mắt: $\mathbf{m}_{\text{eyes}} = \frac{1}{2}(\mathbf{p}_{\text{le}} + \mathbf{p}_{\text{re}})$.
  - Hình chiếu điểm mũi lên trục nối hai mắt: $p_{\text{nose}} = (\mathbf{p}_{\text{nose}} - \mathbf{m}_{\text{eyes}}) \cdot \hat{\mathbf{v}}_{\text{eyes}}$.
  - Độ lệch tâm chuẩn hóa: $\text{offset}_{\text{sym}} = \frac{|p_{\text{nose}}|}{d_{\text{eye}} / 2}$.
  - Tỷ lệ khoảng cách từ mũi tới hai mắt: $r_{\text{sym}} = \frac{\min(d(\text{nose}, \text{le}), d(\text{nose}, \text{re}))}{\max(d(\text{nose}, \text{le}), d(\text{nose}, \text{re}))}$.
  - Khi nhìn thẳng vào bài thi: $\text{offset}_{\text{sym}} < 0.24$ và $r_{\text{sym}} \ge 0.58 \implies S_{\text{yaw}} = 0.0$.
  - Khi tư thế đầu lệch nghi vấn: $\text{offset}_{\text{sym}} \ge 0.28$ hoặc $r_{\text{sym}} < 0.52 \implies S_{\text{yaw}} = \max(s_{\text{offset}}, s_{\text{ratio}}) \in [0.0, 1.0]$.
  - Trường hợp che mũi (đeo khẩu trang): dựa trên khoảng cách giữa trung điểm mắt và trung điểm tai $d(\mathbf{m}_{\text{eyes}}, \mathbf{m}_{\text{ears}}) / d_{\text{eye}}$.
  - Bất đối xứng che khuất tai (Ear Occlusion Asymmetry): nếu một tai có confidence $> 0.35$ và tai đối diện $< 0.15$, $S_{\text{ear\_asym}} = 0.65$.
- **Bộ lọc làm mượt (Smoothing Filter):**  
  Tọa độ pixel $(x, y)$ của các điểm mốc có confidence $> 0.15$ được làm mượt qua bộ lọc Exponential Moving Average (EMA) trong lớp `KeypointSmoother` với hệ số $\alpha = 0.75$:
  $$\mathbf{k}_t(x, y) = 0.75 \cdot \mathbf{k}_t^{\text{raw}}(x, y) + 0.25 \cdot \mathbf{k}_{t-1}(x, y)$$
  *Lưu ý:* EMA chỉ áp dụng cho tọa độ pixel $(x,y)$ của điểm mốc giữa các khung hình liên tiếp, không áp dụng cho góc xoay hay điểm số nghi vấn.

### 2. Điểm số Nghi vấn Tư thế Chuẩn hóa (Posture Suspicion Score)
- **Miền giá trị:** Số thực không thứ nguyên nằm trong đoạn **$[0.0, 1.0]$**:
  $$S_{\text{posture}} = \max(S_{\text{yaw}}, S_{\text{ear\_asym}}) \in [0.0, 1.0]$$
- **Công thức suy diễn `turn_deg = disp_deg`:**
  ```python
  disp_deg = (
      detected_yaw_deg
      if (head_turn_score > 0.15 and detected_yaw_deg > 0)
      else (head_turn_score * 45.0 if head_turn_score > 0.15 else 0.0)
  )
  ```
  *(Ghi chú bắt buộc: Tên trường `turn_deg` là tên trường tương thích giao diện; giá trị là chỉ số trực quan hóa suy ra từ heuristic, không phải phép đo góc vật lý).*
- **Ngưỡng nghi vấn mặc định (`suspicion_threshold`):** Giá trị mặc định là **`0.50`** (có thể tinh chỉnh trong cấu hình từ `0.10` đến `1.00`). Khi điểm số vượt ngưỡng này, trạng thái của thí sinh chuyển sang nghi vấn.

### 3. Quy tắc Bảo vệ Tính Liên tục Thời gian (Temporal Continuity Guard)
- **Thời gian yêu cầu tối thiểu (`posture_alert_seconds`):** Mặc định **`1.25 giây`** (có thể cấu hình).
- **Nguyên lý hoạt động:**  
  Một chuyển động quay đầu chỉ kích hoạt sự cố Cờ Đỏ khi điểm nghi vấn tư thế liên tục duy trì $\ge 0.50$ trong suốt khoảng thời gian $\ge 1.25$ giây tính theo mốc thời gian thực của khung hình.
  - Nếu thí sinh quay đầu nhìn nhanh sang bên cạnh trong 0.4 giây rồi quay lại ngay: hệ thống chỉ hiển thị Cờ Vàng cảnh báo trên màn hình, không kích hoạt sự cố và không cắt clip bằng chứng.
  - Nếu thí sinh duy trì nhìn sang bài thi của bạn bên cạnh $> 1.25$ giây liên tục: hệ thống kích hoạt sự cố Cờ Đỏ `HEAD_TURNING` và gửi lệnh trích xuất clip bằng chứng sang RingBuffer.

### 4. Thuật toán Bám vết Ẩn danh (ByteTrack)
- Hệ thống tích hợp thuật toán ByteTrack của Ultralytics để cấp phát một mã số `track_id` số nguyên tạm thời cho mỗi thí sinh xuất hiện trong khung hình.
- Trường `track_id` là định danh kỹ thuật trong luồng xử lý để liên kết các detection qua thời gian, không đại diện cho danh tính thực tế của thí sinh. Mọi dữ liệu bám vết được đặt lại khi kết thúc phiên hoặc gọi lệnh `/api/session/reset`. Không liên kết với bất kỳ cơ sở dữ liệu danh tính nào.

### 5. Phân Định Minh Bạch Các Cấp Độ Kiểm Chứng:
- **Đã kiểm chứng bằng Code Inspection:** Các chỉ số index điểm mốc COCO, công thức tính toán tỷ lệ hình học, công thức lọc mượt EMA $\alpha=0.75$ cho tọa độ pixel, tích hợp ByteTrack.
- **Đã kiểm chứng bằng Synthetic Test:** Logic bộ đếm thời gian liên tục 1.25s, điều kiện kích hoạt sự cố Cờ Đỏ, cơ chế cooldown 6.0s chống spam sự cố lặp lại (`test_02`, `test_20`, `test_26`, `test_28`).
- **Chưa được kiểm chứng thực nghiệm ngoài đời (Open Blocker):** Chưa có tập dữ liệu video phòng thi thực tế được gán nhãn ground-truth mốc thời gian (onset/offset ground truth) để đo đạc các chỉ số khoa học định lượng (tIoU, Event F1-score, sai số mốc thời gian bắt đầu Onset Error). **Khóa chặn D-03 tiếp tục là `OPEN`**.

---

## F. BACKEND, CƠ SỞ DỮ LIỆU VÀ QUY TRÌNH QUẢN LÝ BẰNG CHỨNG (EVIDENCE WORKFLOW)

### 1. Lược đồ Cơ sở Dữ liệu Sự cố (Incident Schema)
Cơ sở dữ liệu SQLite (`cheating_system.db`) sử dụng bảng duy nhất `incidents` được thiết kế ẩn danh:

```sql
CREATE TABLE incidents (
    id VARCHAR PRIMARY KEY,           -- Mã định danh dạng 'inc_{timestamp}_{hex}'
    student_id VARCHAR NOT NULL,      -- Track ID tạm thời (ví dụ 'Track 1')
    violation_type VARCHAR NOT NULL,  -- 'PHONE' hoặc 'HEAD_TURNING'
    severity VARCHAR NOT NULL,        -- 'yellow' hoặc 'red'
    timestamp DATETIME NOT NULL,      -- Thời điểm vi phạm theo chuẩn UTC ISO 8601
    status VARCHAR DEFAULT 'pending', -- 'pending', 'confirmed', 'dismissed'
    evidence_url VARCHAR,             -- Đường dẫn video MP4 './data/evidence/inc_*.mp4'
    confidence FLOAT                  -- Xác suất độ tin cậy trong đoạn [0.0, 1.0]
);
```

### 2. Hợp đồng Ngữ nghĩa Độ tin cậy (Confidence Contract)
- **Chuẩn hóa Canonical:** Giá trị `confidence` hợp lệ là số thực trong đoạn **$[0.0, 1.0]$**.
- **Tương thích ngược (Legacy Normalization Path):** Nhằm tương thích với các bản ghi cơ sở dữ liệu cũ từng lưu dạng phần trăm, các giá trị trong nửa khoảng $(1.0, 100.0]$ được tự động chia 100 để đưa về $[0.0, 1.0]$. Các giá trị âm, $NaN$, $Infinity$, hoặc $> 100.0$ đều bị từ chối bằng mã lỗi HTTP 422 / ValueError.
- **Rủi ro tồn dư `GAP-SEM-01`:** Nếu giá trị gửi lên là một số nhỏ như `2.0`, hệ thống sẽ chuẩn hóa thành `0.02` (2%) thay vì báo lỗi.

### 3. Vòng Đời Xử lý Bằng chứng Video (Evidence Lifecycle)
1. **Phát sinh tệp tin:** Khi sự cố Cờ Đỏ kích hoạt, `RingBuffer` trích xuất video clip MP4 với cấu trúc đặt tên: `inc_{timestamp_ms}_{hash_hex}.mp4` và lưu vào thư mục cục bộ `./data/evidence/`.
2. **Thời lượng danh định:** Khoảng 5 giây trước thời điểm vi phạm (pre-roll) và 10 giây sau thời điểm vi phạm (post-roll), tổng thời lượng danh định khoảng 15 giây.
3. **Định tuyến chuẩn (Canonical Static Route):** Trình duyệt truy cập tệp bằng chứng qua endpoint tĩnh `/evidence/{filename}`. Route legacy `/api/clips/{filename}` mặc định bị vô hiệu hóa (trả về 404, ẩn khỏi OpenAPI; các payload traversal `..%2F` đều bị chặn an toàn trong kiểm thử).
4. **Hành vi khi Giám thị Phê duyệt:**
   - **Xác nhận (`confirmed`):** Trạng thái bản ghi CSDL đổi thành `confirmed`. Tệp video MP4 trong `./data/evidence/` được **bảo toàn nguyên vẹn** trên đĩa để phục vụ lưu trữ bằng chứng (`test_18`).
   - **Bỏ qua (`dismissed`):** Trạng thái bản ghi CSDL đổi thành `dismissed`. Tệp video MP4 tương ứng được **xóa trong workflow dismiss ở trường hợp đã kiểm thử** nhằm tiết kiệm dung lượng lưu trữ và bảo vệ quyền riêng tư của thí sinh (`test_17`).

### 4. Cơ chế Đảm bảo Đồng thời CSDL (SQLite Concurrency)
- Cơ sở dữ liệu kích hoạt chế độ **Write-Ahead Logging (WAL)**: `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`.
- Thao tác ghi dữ liệu từ các luồng phân tích AI bất đồng bộ được xếp hàng qua `DBWriteQueue`. Một luồng tiến trình nền duy nhất thực thi lệnh ghi tuần tự, tuần tự hóa truy vấn ghi, hạn chế xung đột ghi đồng thời và ngăn chặn lỗi khóa CSDL trong các trường hợp đã kiểm thử (`test_15`, `test_24`).

---

## G. GIAO DIỆN NGƯỜI DÙNG VÀ LUỒNG THAO TÁC (UI & USER FLOWS)

Hệ thống chỉ vận hành **2 giao diện người dùng chính thức (Runtime Views)**:

### 1. Bảng Điều khiển Giám sát Tinh gọn (Streamlined Proctor Dashboard)
- **Khung hình Giám sát Trực tiếp (Live Video Feed):**
  - Hiển thị luồng video thời gian thực từ camera phòng thi hoặc file video.
  - Lớp phủ trực quan (Canvas Overlay): Bounding box màu đỏ quanh điện thoại (`PHONE`), bounding box và khung xương 17 điểm mốc quanh thí sinh, nhãn cảnh báo cờ Vàng/cờ Đỏ và điểm số nghi vấn tư thế.
  - Thanh đo hiệu năng (Telemetry Bar): Hiển thị FPS thu nhận thực tế (Acquisition FPS), FPS suy luận AI (Inference FPS), số lượng gói tin và frame đã xử lý.
- **Bảng Theo dõi Thí sinh Đang hoạt động (Active Student Tracker):**
  - Danh sách các `track_id` ẩn danh đang có mặt trong phòng thi kèm trạng thái hiện tại (Bình thường / Nghi vấn / Vi phạm).
- **Luồng Sự cố Thời gian thực (Incident Stream):**
  - Danh sách các sự cố vi phạm phát sinh theo thứ tự thời gian.
  - Mỗi sự cố hiển thị: Thời điểm, Track ID, Loại vi phạm (`Điện thoại` hoặc `Quay đầu`), Mức độ cảnh báo (Cờ Đỏ), và Nút bấm "Xem Bằng chứng".
- **Hộp thoại Xem lại Video Bằng chứng (Video Evidence Review Modal):**
  - Trình phát video HTML5 phát lại tệp clip MP4 15 giây lấy từ `/evidence/{filename}`.
  - Hai nút hành động:
    - **Nút "Xác nhận Vi phạm" (`Confirm`):** Đổi trạng thái sang `confirmed`, giữ lại tệp video.
    - **Nút "Bỏ qua Sự cố" (`Dismiss`):** Đổi trạng thái sang `dismissed`, xóa tệp video khỏi đĩa cứng.

### 2. Giao diện Cấu hình Trí tuệ Nhân tạo (AI Settings View)
Cho phép giám thị tùy biến độ nhạy của hệ thống phù hợp với từng phòng thi:
- Thanh trượt **Ngưỡng Tin cậy Điện thoại (`phone_conf`):** Mặc định `0.35` (dải điều chỉnh: `0.10` - `0.90`).
- Thanh trượt **Ngưỡng Nghi vấn Quay đầu (`suspicion_threshold`):** Mặc định `0.50` (dải điều chỉnh: `0.10` - `1.00`).
- Thanh trượt **Thời gian Bảo vệ Liên tục (`posture_alert_seconds`):** Mặc định `1.25` giây (dải điều chỉnh: `0.50` - `5.00` giây).
- Các tham số độ dài bộ đệm: Pre-roll (5.0s), Post-roll (10.0s), Cooldown (6.0s).
- **Nút "Làm sạch Phiên" (`Reset Session`):** Đặt lại toàn bộ bộ đếm telemetry, bộ đệm khung hình và xóa bám vết ByteTrack về trạng thái ban đầu mà không làm mất dữ liệu sự cố trong CSDL.

> [!IMPORTANT]
> Toàn bộ các giao diện lịch sử trước đây (`public/screens/` gồm 12 tệp HTML mockups về ma trận phòng thi, sơ đồ chỗ ngồi, lập biên bản vi phạm) đã được gỡ bỏ hoàn toàn khỏi mã nguồn sản phẩm. Chúng được phân loại chính thức là **`ARCHIVED_NON_RUNTIME`** hoặc **`legacy asset removed; request resolves to generic SPA fallback, not legacy content`**.

---

## H. TỔNG HỢP THỰC NGHIỆM HỆ THỐNG ĐÃ HOÀN THÀNH (EMPIRICAL BENCHMARKS)

Bảng tổng hợp toàn bộ các thực nghiệm định lượng đã thực thi trực tiếp trên hệ thống mã nguồn hiện tại:

| Tên Thực Nghiệm | Môi Trường Thực Thi | Dữ Liệu Đầu Vào | Chỉ Số Đo Đạc (Metrics) | Kết Quả Thực Tế Đạt Được | Nguồn Bằng Chứng | Giới Hạn Diễn Giải Khoa Học |
|---|---|---|---|---|---|---|
| **Kiểm thử Thu nhận & Vận chuyển End-to-End Trình duyệt (E2E Benchmark)** | Windows 10/11, Trình duyệt Edge/Chrome, Python 3.12 Backend, CPU i7/Ryzen | Luồng webcam giả lập chuẩn 15 FPS, thời lượng phiên 125,1 giây | - Tốc độ toàn phiên (Global Session Rates)<br>- Chỉ số telemetry cửa sổ trượt (Rolling Window Telemetry)<br>- Counter dropped<br>- Đẳng thức bảo toàn hàng đợi | - **Toàn phiên (125,1s):** Capture 15,60 FPS (1.952 frames), Sent 15,60 FPS (1.952 frames), Server Ingestion 15,58 FPS (1.949 frames), Server Inference 2,29 FPS (287 frames), Superseded 85,27% (1.662 frames)<br>- **Cửa sổ trượt:** Acquisition mean 15,88 FPS (P50: 15,00, P95: 19,00), Inference mean 2,77 FPS, Latency trung bình 360,4 ms<br>- **Chênh lệch sent/received:** Tại thời điểm kết thúc phép đo, bộ đếm phía client ghi nhận 1.952 frame đã gửi và bộ đếm phía server ghi nhận 1.949 frame đã nhận, chênh lệch 3 frame. Artifact hiện có không đủ để xác định nguyên nhân chính xác của chênh lệch này.<br>- **Counter dropped:** Counter `client_backpressure_drops` (map sang `transport_dropped_frames`) không ghi nhận frame bị loại bởi điều kiện socket chưa mở, bufferedAmount > 64KB hoặc lỗi ws.send() trong phiên kiểm thử.<br>- **Bảo toàn số học:** $\text{processed } (287) + \text{superseded } (1662) + \text{pending } (0) = \text{submitted } (1949)$. | `reports/evidence/report_runtime/e2e_benchmark_result.json`, `test_26`, `test_28` | Đo đạc trên môi trường máy trạm thử nghiệm CPU cục bộ. Tốc độ suy luận AI sẽ thay đổi khi có phần cứng chuyên dụng. |
| **Bảo toàn Bất biến Telemetry Phiên (Session Invariants)** | Backend Test Runner (`unittest`) | 3 luồng WebSocket kết nối đồng thời và tuần tự | - Inv 4: decoded $\le$ received<br>- Inv 5: submitted $\le$ decoded<br>- Inv 6: processed + superseded + pending = submitted<br>- Inv 7: results sent $\le$ processed | - Tất cả 4 bất biến toán học: **TRUE** trong suốt phiên<br>- Backlog depth bound: **$\le 1$ ở mọi thời điểm**<br>- Trễ tích lũy: **được ngăn ngừa chủ động qua buffer đơn slot** | `backend/tests/test_refactored_system.py:test_28` | Xác minh tính đúng đắn của giải thuật điều phối bộ đệm đơn; không phản ánh chất lượng nhận diện của mô hình. |
| **Bộ Kiểm thử Hồi quy Backend (Backend Regression Suite)** | Python 3.12, SQLite 3 WAL, FastAPI TestClient | 31 kịch bản kiểm thử tích hợp toàn diện | Tỷ lệ vượt qua (Pass rate), tính toàn vẹn CSDL, quản lý clip MP4, phòng chống path traversal | **31 / 31 tests PASS** trong thời gian 9.59 giây | `backend/tests/test_refactored_system.py` | Các bộ kiểm thử được cấu hình đã pass; không tự suy diễn thành "mọi bài kiểm thử trong dự án". |
| **Bộ Kiểm thử Đánh giá Độc lập (Evaluation Harness Suite)** | Python 3.12, mô-đun toán học đánh giá độc lập | 22 bài unit test kiểm tra công thức toán và cấu hình dữ liệu | Tính toàn vẹn YAML, kiểm tra leakage, thuật toán AP, khớp sự kiện thời gian (tIoU, event matching) | **22 / 22 tests PASS** trong thời gian 0.27 giây | `scripts/evaluation/tests/test_evaluation_harness.py` | Kiểm chứng tính chính xác của bộ công cụ đánh giá (harness); chưa nạp dữ liệu kiểm thử thực tế ngoài đời. |
| **Bộ Kiểm thử Hợp đồng Telemetry Frontend** | Node.js / tsx runner | 10 kịch bản phân giải payload WebSocket | Tính toàn vẹn kiểu dữ liệu và 8 trường telemetry | **10 / 10 assertions PASS** | `src/services/__tests__/test_telemetry_contract.ts` | Xác minh tầng giải mã giao thức phía Client; không đo lường giao diện đồ họa. |
| **Kiểm tra Kiểu Tĩnh TypeScript (Static Typecheck)** | Trình biên dịch `tsc` (TypeScript 5.x) | Toàn bộ mã nguồn thư mục `src/` | Số lượng lỗi biên dịch kiểu tĩnh (Compilation Errors) | **0 LỖI (Exit code 0)** | Lệnh thực thi: `npx tsc --noEmit` | Xác minh tính an toàn kiểu tĩnh; chưa phải bộ linter AST toàn diện (`GAP-TOOL-01`). |
| **Biên dịch Xuất xưởng Frontend (Production Build)** | Vite 6.4.3 | Mã nguồn React 19 và các tài nguyên tĩnh | Khả năng đóng gói thành công, kích thước bundle, không rò rỉ mã cũ | **THÀNH CÔNG (Exit code 0)**, thời gian 1.97s. `dist/index.html` 0.88 kB, không chứa tệp legacy. | Lệnh thực thi: `npm run build` | Chứng minh ứng dụng sẵn sàng triển khai tĩnh cục bộ; không phụ thuộc CDN bên ngoài. |
| **Kiểm tra Phân giải URL Tĩnh & SPA Fallback** | Python HTTP Client, Vite Dev Server | Các URL cũ `/screens/*.html` và `/avatars/*.jpg` | Mã trạng thái HTTP, MIME type, nội dung trả về | Request phân giải chính xác: `Legacy asset removed; request resolves to generic SPA fallback, not legacy content` (HTTP 200, 1.048B text/html, không rò rỉ nội dung cũ) | `scripts/verify_legacy_assets.py` | Xác minh cơ chế định tuyến máy chủ phát triển; ứng dụng chính không gọi đến các tài nguyên này. |

---

## I. PHÂN LOẠI KẾT QUẢ MÔ HÌNH ĐƯỢC PHÉP TRÌNH BÀY

Để bảo đảm tính trung thực khoa học trong Báo cáo KHKT, toàn bộ kết quả mô hình được phân định rõ ràng thành 3 nhóm:

### 1. Nhóm `TRAINING_VALIDATION_ONLY` (Chỉ số Huấn luyện & Kiểm định Nội bộ Lịch sử)
*Chỉ được phép trình bày trong mục "Lịch sử và Quá trình Huấn luyện Mô hình", bắt buộc đi kèm chú thích nguồn từ `results.csv` và không đại diện cho hiệu năng thực tế:*
- Tốc độ hội tụ qua 60 epoch: Precision tăng từ 0.354 (epoch 1) lên cực đại 0.804 (epoch 53); Recall tăng từ 0.312 (epoch 1) lên cực đại 0.704 (epoch 59).
- Điểm số mAP@0.5 cao nhất: **78.58%** (đạt được tại Epoch 55).
- Điểm số mAP@0.5 ở Epoch 60: **76.92%**.
- Điểm số mAP@0.5:0.95 ở Epoch 60: **47.16%**.
- Kích thước tệp trọng số `phone_detector_v5.pt`: **19.25 MB** (19.245.082 byte).

### 2. Nhóm `SYSTEM_RUNTIME_VERIFIED` (Chỉ số Vận hành Hệ thống Đã Kiểm chứng)
*Được phép đưa vào phần "Kết quả Thực nghiệm Hệ thống":*
- Tốc độ thu nhận và gửi toàn phiên (125,1s): **15,60 FPS** (1.952 frame capture và sent); tốc độ nhận máy chủ toàn phiên: **15,58 FPS** (1.949 frame received); tốc độ suy luận hoàn thành toàn phiên: **2,29 FPS** (287 frame processed).
- Telemetry cửa sổ trượt: Tốc độ thu nhận trung bình **15,88 FPS** (P50: 15,00, P95: 19,00); tốc độ suy luận CPU trung bình **2,77 FPS** với độ trễ tính toán trung bình **360,4 ms**.
- Chênh lệch gửi/nhận: Tại thời điểm kết thúc phép đo, bộ đếm phía client ghi nhận 1.952 frame đã gửi và bộ đếm phía server ghi nhận 1.949 frame đã nhận, chênh lệch 3 frame. Artifact hiện có không đủ để xác định nguyên nhân chính xác của chênh lệch này.
- Counter dropped: Counter `client_backpressure_drops` (map sang `transport_dropped_frames`) không ghi nhận frame bị loại bởi điều kiện socket chưa mở, bufferedAmount > 64KB hoặc lỗi ws.send() trong phiên kiểm thử.
- Tỷ lệ superseded: **85,27%** (1.662 frame); các frame trung gian được thay thế có chủ đích trong single-slot inference buffer để worker luôn xử lý frame mới nhất; đây không phải lỗi truyền tải.
- Đẳng thức bảo toàn: $\text{processed } (287) + \text{superseded } (1662) + \text{pending } (0) = \text{submitted } (1949)$.
- Thời gian tạo clip bằng chứng ~15 giây và ghi CSDL: bất đồng bộ, không làm gián đoạn luồng video chính.

### 3. Nhóm `BLOCKED_PENDING_EVALUATION` (Chưa Đánh giá - Khóa chặn Chờ Dữ liệu)
*Tuyệt đối không công bố bất kỳ con số nào; ghi nhận minh bạch là khoảng trống nghiên cứu:*
- **Mô hình Điện thoại:** Chưa có mAP, Precision, Recall trên tập kiểm thử độc lập (D-02: tập đánh giá độc lập, chưa từng tham gia train, validation, điều chỉnh threshold hoặc kiểm thử thủ công trước đó, đồng thời đại diện hợp lý cho bối cảnh sử dụng dự kiến; OOD evaluation là một đánh giá bổ sung, tách biệt với D-02). *(Bị chặn bởi Khóa chặn D-02)*.
- **Phát hiện Hành vi Quay đầu:** Chưa có tIoU, Event F1-score, sai số mốc thời gian bắt đầu (Onset Error) trên tập video phòng thi thực tế có nhãn chuẩn. *(Bị chặn bởi Khóa chặn D-03)*.

---

## J. CÁC HẠN CHẾ VÀ RỦI RO CÒN LẠI (LIMITATIONS & RESIDUAL RISKS)

Báo cáo KHKT bắt buộc phải trình bày trung thực các hạn chế kỹ thuật sau:
1. **Khóa chặn D-02 Chưa Đóng (Open Independent Holdout):** Hiệu năng của mô hình phát hiện điện thoại mới chỉ được kiểm chứng trên tập validation nội bộ lịch sử, chưa có tập holdout độc lập (D-02: tập đánh giá độc lập, chưa từng tham gia train, validation, điều chỉnh threshold hoặc kiểm thử thủ công trước đó, đồng thời đại diện hợp lý cho bối cảnh sử dụng dự kiến) đủ đại diện cho các điều kiện phòng thi thực tế đa dạng. OOD evaluation là một đánh giá bổ sung, tách biệt với D-02.
2. **Khóa chặn D-03 Chưa Đóng (Open Event Benchmark):** Thuật toán phát hiện quay đầu mới chỉ vượt qua các bài kiểm thử giả lập (synthetic tests); chưa được đánh giá định lượng trên video phòng thi thực tế có gán nhãn mốc thời gian.
3. **Chưa Đánh giá Rò rỉ Dữ liệu Gần giống (Near-duplicate Leakage):** Quá trình kiểm toán chỉ xác minh không có trùng lặp mã băm tuyệt đối (exact hash) giữa các tập dữ liệu. Khả năng tồn tại các khung hình liền kề trích xuất từ cùng một video clip nguồn (session correlation) giữa tập train và valid chưa được kiểm soát bằng perceptual hashing.
4. **Trạng thái Checkpoint Khởi đầu và Best Epoch Chưa Xác Định:** Không thể chứng minh bằng artifact rằng mô hình ban đầu bắt đầu từ `yolo11s.pt` chuẩn hay một checkpoint khác (`initial_pretrained_checkpoint_status = UNRESOLVED`), và chưa xác định được chính xác epoch nào sinh ra file `best.pt` (`best_checkpoint_source_epoch_status = UNRESOLVED`).
5. **Rủi ro Ngữ nghĩa Chuẩn hóa Confidence (`GAP-SEM-01`):** Do cơ chế tương thích ngược hỗ trợ dữ liệu phần trăm cũ ($> 1.0$ chia 100), giá trị lỗi như `2.0` sẽ bị hiểu thành `0.02` thay vì bị từ chối.
6. **Công cụ Linter Frontend Chưa Hoàn thiện (`GAP-TOOL-01`):** Lệnh `npm run lint` hiện chỉ là alias gọi trình biên dịch kiểu tĩnh `tsc --noEmit`, chưa cấu hình bộ quy tắc phân tích cú pháp AST độc lập (ESLint / Biome).
7. **Độ nhạy với Điều kiện Thực tế:** Hệ thống thị giác máy tính phụ thuộc vào chất lượng camera, điều kiện ánh sáng phòng thi (bị tối hoặc ngược sáng mạnh), góc đặt camera (quá cao hoặc góc nghiêng quá lớn làm biến dạng tỷ lệ hình học), và hiện tượng che khuất (thí sinh cúi người che khuất ngực hoặc điện thoại bị khuất sau tay áo).
8. **Giới hạn Hỗ trợ Quyết định:** Hệ thống chỉ là công cụ hỗ trợ quan sát; mọi kết luận vi phạm bắt buộc phải có sự thẩm định và xác nhận trực tiếp của giám thị phòng thi.

---

## K. ĐẠO ĐỨC VÀ BẢO VỆ QUYỀN RIÊNG TƯ (ETHICS & PRIVACY)

Incident schema không yêu cầu tên, SBD, CCCD hoặc email. Runtime không thực hiện nhận diện danh tính và không tạo face embedding. Tuy nhiên, frame và clip có thể chứa hình ảnh nhận dạng được của người dự thi nên vẫn phải được quản lý như dữ liệu cá nhân phù hợp với quy định áp dụng.

Trường `track_id` là định danh kỹ thuật trong luồng xử lý để liên kết các detection qua thời gian, không đại diện cho danh tính thực tế của thí sinh.

Vòng đời dữ liệu tuân thủ đúng hiện trạng triển khai kỹ thuật: trong phiên giám sát, khung hình được luân chuyển trong bộ đệm vòng (`RingBuffer`) và hàng đợi đơn slot (`SingleSlotInferenceBuffer`). Clip bằng chứng chỉ được trích xuất và ghi ra tệp MP4 khi phát sinh sự cố. Nếu giám thị chọn Bỏ qua (`Dismiss`), tệp clip bằng chứng tương ứng được xóa trong quy trình xử lý sự cố đã kiểm thử; nếu chọn Xác nhận (`Confirm`), tệp clip được lưu giữ tại `./data/evidence/` trên máy trạm cục bộ phục vụ công tác đối soát của Hội đồng thi.

Các giải pháp trên là những lựa chọn thiết kế kỹ thuật nhằm giảm thiểu dữ liệu thu thập và xử lý, không cấu thành một chứng nhận tuân thủ pháp lý chính thức (như GDPR hay chứng chỉ an toàn thông tin chuyên biệt) do chưa qua quy trình thẩm định của cơ quan quản lý độc lập.

---

## L. ĐÓNG GÓP CỦA CÁC THÀNH VIÊN NGHIÊN CỨU (CONTRIBUTIONS)

*(Bảng phân công trách nhiệm kỹ thuật và đóng góp; PM và các tác giả sẽ điền thông tin hành chính chính thức sau)*:

| Thành Viên / Vai Trò | Phân Công Trách Nhiệm Kỹ Thuật Chính | Tỷ Lệ Đóng Góp Dự Kiến | Ghi Chú Xác Nhận |
|---|---|:---:|---|
| **`[THÀNH VIÊN 1 — Người huấn luyện mô hình điện thoại]`** | - Thu thập và tổng hợp dữ liệu từ 3 gói Roboflow nguồn.<br>- Thiết lập siêu tham số và huấn luyện mô hình YOLO11s (`phone_detector_v5.pt`).<br>- Trích xuất và bàn giao gói bằng chứng lịch sử Pass 1.3. | `[CẦN XÁC NHẬN: ...%]` | Chờ PM/Tác giả điền tên chính thức |
| **`[THÀNH VIÊN 2 — Kỹ sư Phần mềm, UI, Backend, Tích hợp]`** | - Thiết kế kiến trúc hai pipeline (RingBuffer & SingleSlotInferenceBuffer).<br>- Xây dựng backend FastAPI, hàng đợi `DBWriteQueue`, CSDL SQLite WAL.<br>- Phát triển thuật toán bóc tách tư thế quay đầu và Temporal Continuity Guard.<br>- Lập trình giao diện giám thị Streamlined Proctor Dashboard (React 19).<br>- Xây dựng bộ harness đánh giá mô hình và 31 bài kiểm thử tự động. | `[CẦN XÁC NHẬN: ...%]` | Chờ PM/Tác giả điền tên chính thức |
| **`[GIÁO VIÊN HƯỚNG DẪN / CỐ VẤN KHOA HỌC]`** | - Định hướng phương pháp nghiên cứu khoa học và phạm vi đề tài.<br>- Rà soát tính chặt chẽ của các phép đo thực nghiệm và đạo đức nghiên cứu. | `[CẦN XÁC NHẬN]` | Chờ PM/Tác giả điền tên chính thức |

---

## M. DANH MỤC HÌNH ẢNH, BẢNG BIỂU VÀ TÀI NGUYÊN CHO BÁO CÁO KHKT

| Ký Hiệu | Tên Hình Ảnh / Bảng Biểu / Tài Nguyên | Nguồn Tạo / File Căn Cứ | Trạng Thái Hiện Tại | Hành Động Cần Thiết Khi Viết Bản Cuối |
|:---:|---|---|:---:|---|
| **Hình 1** | Sơ đồ Kiến trúc Hệ thống Hai Pipeline Bất đồng bộ | Sơ đồ Mermaid trong Section C | **`AVAILABLE`** | Kết xuất thành hình ảnh vector / PNG độ nét cao |
| **Hình 2** | Sơ đồ Luồng Trích xuất và Xử lý Bằng chứng Video ~15s | `backend/services/ring_buffer.py` | **`AVAILABLE`** | Vẽ sơ đồ tuần tự (Sequence Diagram) chi tiết pre/post roll |
| **Hình 3** | Sơ đồ 17 Điểm Mốc COCO và Hình học Điểm Nghi vấn Tư thế Đầu | `model/exam_analyzer.py` | **`AVAILABLE`** | Vẽ minh họa trực quan các điểm mũi, mắt, tai và khoảng cách hình học |
| **Hình 4** | Lược đồ Quan hệ Thực thể (ERD) Bảng `incidents` CSDL | `backend/models.py` | **`AVAILABLE`** | Trích xuất biểu đồ cấu trúc bảng SQLite |
| **Hình 5** | Ảnh chụp Màn hình Giao diện Bảng Điều khiển Giám sát Live | `src/components/StreamlinedProctorDashboard.tsx` | **`NEEDS_CAPTURE`** | Chụp ảnh thực tế giao diện đang chạy kèm bounding box và telemetry |
| **Hình 6** | Ảnh chụp Màn hình Hộp thoại Xem lại Video Bằng chứng | `src/components/modals/VideoEvidenceModal.tsx` | **`NEEDS_CAPTURE`** | Chụp ảnh thực tế modal phát video và nút bấm Xác nhận/Bỏ qua |
| **Hình 7** | Ảnh chụp Màn hình Giao diện Cấu hình AI Settings | `src/components/views/AiSettingsView.tsx` | **`NEEDS_CAPTURE`** | Chụp ảnh giao diện các thanh trượt điều chỉnh ngưỡng |
| **Hình 8** | Biểu đồ Diễn biến Huấn luyện 60 Epoch (Loss, mAP, Precision, Recall) | `reports/evidence/training_lineage/results.csv` | **`AVAILABLE`** | Dùng matplotlib vẽ đồ thị 4 trục từ file `results.csv` |
| **Hình 9** | Biểu đồ Tốc độ Thu nhận và Phân phối Trễ Frame E2E | `reports/evidence/report_runtime/e2e_benchmark_result.json` | **`AVAILABLE`** | Vẽ đồ thị histogram phân phối FPS và thời gian trễ suy luận |
| **Bảng 1** | Bảng Phân bố Dữ liệu Tập `phone_merged` và 3 Nguồn Roboflow | `reports/evidence/training_lineage/lineage_manifest.json` | **`AVAILABLE`** | Đã sẵn sàng số liệu chính xác |
| **Bảng 2** | Bảng Siêu tham số Huấn luyện Mô hình YOLO Phone | `reports/evidence/training_lineage/args.yaml` | **`AVAILABLE`** | Đã sẵn sàng số liệu chính xác |
| **Bảng 3** | Bảng So sánh Hiệu năng E2E và Bất biến Toán học Telemetry | `reports/evidence/report_runtime/e2e_benchmark_result.json`, `test_28` | **`AVAILABLE`** | Đã sẵn sàng số liệu chính xác |
| **Bảng 4** | Bảng Kết quả 31 Bài Kiểm thử Hồi quy Backend | `backend/tests/test_refactored_system.py` | **`AVAILABLE`** | Đã sẵn sàng số liệu chính xác |
| **Bảng 5** | Bảng Kết quả Đánh giá Mô hình trên Tập Holdout Độc lập | N/A (Chờ dữ liệu D-02) | **`BLOCKED`** | Bị chặn bởi Khóa chặn D-02 (để trống hoặc ghi chú tương lai) |
| **Bảng 6** | Bảng Kết quả Đánh giá Phát hiện Quay đầu trên Video Thực tế | N/A (Chờ dữ liệu D-03) | **`BLOCKED`** | Bị chặn bởi Khóa chặn D-03 (để trống hoặc ghi chú tương lai) |

---
**KẾT THÚC REPORT SOURCE PACK (RPT-SRC-V4.0)**
