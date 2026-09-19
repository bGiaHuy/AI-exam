# 🔒 ĐẶC TẢ ĐÓNG BĂNG PHẠM VI HỆ THỐNG (SYSTEM SCOPE FREEZE)
## DỰ ÁN: AI-POWERED AUTOMATED PROCTORING SYSTEM (AI EXAM CONTROL)
**Mã văn bản:** `SPEC-SCOPE-FREEZE-V3.0`  
**Ngày ban hành:** 14/09/2026  
**Trạng thái:** CHÍNH THỨC ĐÓNG BĂNG (FROZEN & RATIFIED)  
**Môi trường triển khai:** Máy trạm giám thị cục bộ (Offline On-Premise, Localhost only)  

---

## 1. MỤC ĐÍCH VĂN BẢN
Văn bản này xác lập ranh giới kỹ thuật tối hậu cho hệ thống **AI Exam Control**. Toàn bộ mã nguồn phát triển, cơ sở dữ liệu, mô hình trí tuệ nhân tạo, quy trình kiểm thử và tài liệu báo cáo Khoa học Kỹ thuật (KHKT) bắt buộc phải tuân thủ nghiêm ngặt theo các nội dung được định nghĩa dưới đây. Bất kỳ chức năng, cấu trúc dữ liệu hoặc thuật ngữ nào nằm ngoài văn bản này đều bị coi là **vi phạm phạm vi sản phẩm (Out of Scope)**.

---

## 2. PHẠM VI SẢN PHẨM CHÍNH THỨC (OFFICIAL IN-SCOPE)

Hệ thống AI Exam Control chỉ thực hiện duy nhất **09 chức năng cốt lõi** sau:

1. **Tiếp nhận luồng video (Video Ingestion):**
   - Tiếp nhận luồng khung hình (video frames) từ Webcam kết nối trực tiếp với máy trạm hoặc tập tin video tải lên thông qua trình duyệt web.
   - Truyền tải khung hình nhị phân liên tục thời gian thực qua giao thức WebSocket nhị phân (`/api/ws/ingest`).

2. **Phát hiện điện thoại di động (`PHONE`):**
   - Sử dụng mô hình học sâu thị giác máy tính (`phone_detector_v5.pt`) để phát hiện sự hiện diện của điện thoại trong khu vực làm bài thi của thí sinh.

3. **Phát hiện hành vi quay đầu / tư thế nghi vấn (`HEAD_TURNING`):**
   - Sử dụng mô hình ước lượng tư thế (`yolo11m-pose.pt`) trích xuất 17 điểm khung xương theo chuẩn COCO (đặc biệt là mũi, mắt, tai, vai).
   - Áp dụng giải thuật heuristic từ hình học xạ ảnh 2D của các keypoint COCO (mắt, mũi, tai, vai) để tính điểm nghi vấn tư thế đầu chuẩn hóa, kết hợp quy tắc thời gian thực (`posture_alert_seconds >= 1.25s`) để nhận diện hành vi quay đầu nhìn bài.

4. **Hiển thị cảnh báo trực quan cho giám thị (Proctor HUD & Alerts):**
   - Cảnh báo **Cờ Vàng (`yellow` / `SUSPICIOUS`)**: Hiển thị khung bao (bounding box) và cảnh báo trực tiếp trên màn hình giám sát khi phát hiện tư thế đầu bất thường nhưng chưa vượt ngưỡng thời gian leo thang.
   - Cảnh báo **Cờ Đỏ (`red` / `CHEATING_POSTURE` hoặc `PHONE`)**: Hiển thị cảnh báo nguy cấp khi phát hiện điện thoại di động hoặc hành vi quay đầu kéo dài liên tục $\ge 1.25$ giây.

5. **Theo dõi đối tượng ẩn danh (Anonymous Object Tracking):**
   - Sử dụng thuật toán ByteTrack gán mã định danh tạm thời (`track_id`: số nguyên 1, 2, 3...) cho từng người quan sát được trong phạm vi phiên thi hiện tại.
   - Mã số này thuần túy phục vụ theo dõi chuyển động cơ học qua các khung hình liên tiếp; **không đại diện cho danh tính thí sinh**.

6. **Trích xuất và lưu trữ video bằng chứng tự động (Evidence Clip Extraction):**
   - Sử dụng bộ đệm vòng tròn thời gian thực (`VideoRingBuffer`) liên tục lưu giữ các khung hình gần nhất.
   - Khi có sự cố Cờ Đỏ (`red`), hệ thống tự động trích xuất đoạn video gồm **khoảng 5.0 giây trước (pre-roll)** và **10.0 giây sau (post-roll)** thời điểm kích hoạt, tổng thời lượng clip ~15.0 giây.
   - Nội suy tái lập thời gian thực (time-grid resampling) đảm bảo video MP4 xuất ra có tốc độ phát tự nhiên 1.0x.
   - Lưu trữ tập tin video `.mp4` và ảnh chụp đỉnh điểm `.jpg` tại `./data/evidence/`.

7. **Lưu trữ siêu dữ liệu sự cố ẩn danh vào SQLite (SQLite Event Persistence):**
   - Lưu trữ nhật ký sự cố vào cơ sở dữ liệu cục bộ SQLite 3 (`./cheating_system.db`) chế độ WAL (Write-Ahead Logging).
   - Toàn bộ thao tác ghi DB được điều phối qua hàng đợi tuần tự an toàn đa luồng (`DBWriteQueue`).
   - Bảng cơ sở dữ liệu duy nhất `incidents` chỉ chứa thông tin kỹ thuật: mã sự cố, nguồn camera, `track_id` ẩn danh, loại vi phạm, độ tin cậy, mức độ nghiêm trọng, mốc thời gian UTC, đường dẫn video/ảnh bằng chứng, trạng thái duyệt và ghi chú giám thị.

8. **Xem lại và đánh giá sự cố (Proctor Review & Verification):**
   - Cho phép giám thị xem lại video bằng chứng MP4 đã trích xuất trực tiếp trên giao diện trình duyệt.
   - Hỗ trợ thao tác cập nhật trạng thái sự cố: **Xác nhận vi phạm (`confirmed`)** hoặc **Bỏ qua / Báo động giả (`dismissed`)** cùng ghi chú nghiệp vụ.

9. **Cấu hình tham số AI & Thu thập Telemetry hệ thống:**
   - Cho phép giám thị điều chỉnh các tham số độ nhạy AI (`phone_confidence`, `posture_alert_seconds`, `suspicion_threshold`, `pre_roll_seconds`, `post_roll_seconds`, `cooldown_seconds`) lưu trữ tại `./data/ai_settings.json`.
   - Thu thập và kiểm chứng các chỉ số đo lường hiệu năng thời gian thực (FPS thu nhận, FPS suy luận, độ trễ, số lượng frame xử lý, tỷ lệ frame bị thay thế, kiểm tra bất biến toán học theo phiên).

---

## 3. CÁC NỘI DUNG NGOÀI PHẠM VI (STRICT NON-GOALS / OUT OF SCOPE)

Nhằm đảm bảo tính khả thi, tính minh bạch và sự tập trung cao độ vào bài toán thị giác máy tính, **các thành phần sau đã được loại bỏ khỏi phạm vi hệ thống**:

| STT | Thành phần loại bỏ | Lý do kỹ thuật & Ranh giới trách nhiệm |
|---|---|---|
| 1 | **Tên thí sinh, Số báo danh (SBD), CCCD, Mã định danh** | Hệ thống không quản lý hồ sơ cá nhân. Mọi phát hiện thị giác hoàn toàn ẩn danh, chỉ định vị theo tọa độ không gian và `track_id` cơ học tạm thời. |
| 2 | **Nhận diện khuôn mặt (Face Recognition / FaceNet)** | Bài toán nhận diện khuôn mặt sinh trắc học đòi hỏi điều kiện ánh sáng, góc chụp chính diện và cơ sở dữ liệu vân khuôn mặt nhạy cảm, không phù hợp camera giám sát từ xa và gây rủi ro quyền riêng tư. |
| 3 | **Điểm danh thí sinh / Check-in tự động** | Nghiệp vụ hành chính đầu giờ thi do giám thị trực tiếp đảm nhiệm; hệ thống AI chỉ tập trung giám sát hành vi trong thời gian làm bài. |
| 4 | **Danh bạ thí sinh / Import danh sách Excel/CSV** | Không cần thiết do hệ thống không duy trì cấu trúc dữ liệu người thi. |
| 5 | **Lập biên bản xử lý vi phạm / In biên bản / Mẫu A1, A2, B1** | Không thực hiện: Nghiệp vụ lập biên bản kỷ luật mang tính pháp lý hành chính nhà trường, cần sự chứng kiến và ký biên bản của hội đồng thi; hệ thống chỉ cung cấp dữ liệu video ghi nhận cùng siêu dữ liệu (metadata) hỗ trợ giám thị xem xét. |
| 6 | **Chữ ký số / Chữ ký điện tử Canvas** | Đã loại bỏ do không còn biểu mẫu biên bản trên phần mềm. |
| 7 | **Trợ lý hỏi đáp quy chế thi (RAG) / Chatbot AI** | Các mô hình ngôn ngữ lớn (LLM/RAG) tiêu tốn tài nguyên GPU, mang tính trang trí, dễ gây ảo giác (hallucination) và không phục vụ mục tiêu giám sát thị giác thời gian thực. |
| 8 | **Điểm liêm chính cá nhân hóa (Integrity Score)** | Không tính toán trừ điểm tích lũy của từng cá nhân vì không định danh danh tính và để tránh thiên kiến sai số mô hình. |
| 9 | **Theo dõi danh tính xuyên suốt ngoài phiên (Cross-session Re-ID)** | `track_id` được reset hoàn toàn về 0/1 khi bắt đầu phiên mới hoặc khi ngắt kết nối WebSocket. Không có cơ chế Re-ID người qua nhiều camera hoặc qua các buổi thi khác nhau. |
| 10 | **Phát hiện âm thanh, tiếng ồn, nhắc bài bằng giọng nói** | Phần cứng micro trong phòng thi lớn thường nhiễu tạp âm (quạt trần, xe cộ, tiếng thở), tỷ lệ báo động giả cực cao; hệ thống chỉ tập trung vào thị giác. |
| 11 | **Phát hiện phao thi giấy siêu nhỏ / Rời khỏi chỗ ngồi** | Phao giấy có kích thước quá nhỏ ngoài độ phân giải hữu dụng của camera tổng quan; rời khỏi chỗ ngồi là nghiệp vụ giám sát vật lý hiển nhiên của giám thị tại chỗ. |

---

## 4. ĐỐI TƯỢNG NGƯỜI DÙNG HỆ THỐNG (SYSTEM PERSONAS)

Hệ thống được thiết kế phục vụ duy nhất một vai trò người dùng:

- **Giám thị phòng thi / Người vận hành máy trạm (Proctor / System Operator):**
  - **Môi trường thao tác:** Ngồi trực tiếp trước máy trạm giám sát cục bộ đặt tại bàn giám thị hoặc phòng hội đồng thi.
  - **Mục tiêu công việc:** Quan sát luồng camera trực tiếp, nhận thông báo cảnh báo tức thì khi có nghi vấn vi phạm, kiểm tra video clip bằng chứng đã trích xuất, xác nhận hoặc loại bỏ cảnh báo giả, và điều chỉnh độ nhạy mô hình phù hợp với điều kiện phòng thi.
  - **Quyền hạn:** Toàn quyền vận hành ứng dụng cục bộ; không yêu cầu phân quyền đăng nhập đa cấp bậc, không kết nối tài khoản đám mây.

---

## 5. CÁC LUỒNG NGHIỆP VỤ CHUẨN (STANDARDIZED WORKFLOWS)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LUỒNG NGHIỆP VỤ CHUẨN                           │
└────────────────────────────────────────────────────────────────────────┘

 [1. KHỞI TẠO PHIÊN]
        │
        ▼
   Trình duyệt kết nối WebSocket nhị phân (`/api/ws/ingest?session_id=...`)
   Máy chủ reset toàn bộ trạng thái phiên cũ (ByteTrack, Buffer, Cooldown)
        │
        ▼
 [2. GIÁM SÁT THỜI GIAN THỰC]
        │
        ├──► Gửi khung hình JPEG (15 FPS, đóng gói 16 bytes header nhị phân)
        ├──► Máy chủ đẩy khung hình vào RingBuffer (dung lượng 20-30 giây)
        └──► Handoff sang hàng đợi suy luận Single-Slot (Backlog depth <= 1)
        │
        ▼
 [3. PHÂN TÍCH & PHÁT HIỆN THỊ GIÁC]
        │
        ├──► YOLO Pose ước lượng 17 keypoints -> EMA Filter -> Tính điểm nghi vấn tư thế đầu
        └──► YOLO Phone phát hiện điện thoại di động trong khung hình
        │
        ▼
 [4. PHÂN LOẠI & LEO THANG CẢNH BÁO]
        │
        ├──► Điểm nghi vấn tư thế đầu duy trì < 1.25s:
        │       └─► Gửi CỜ VÀNG (Hiển thị HUD trên Dashboard, KHÔNG tạo clip)
        │
        └──► Phát hiện Điện thoại HOẶC Điểm nghi vấn tư thế đầu duy trì >= 1.25s:
                └─► Kích hoạt CỜ ĐỎ (Gửi WebSocket event, kích hoạt RingBuffer)
        │
        ▼
 [5. XUẤT CLIP BẰNG CHỨNG & LƯU TRỮ TRẦN]
        │
        ├──► RingBuffer giữ 5.0s pre-roll + ghi tiếp 10.0s post-roll
        ├──► Resampling trên lưới thời gian thực (đảm bảo tốc độ phát 1.0x)
        ├──► Kiểm tra tính toàn vẹn file MP4 bằng OpenCV (size > 0, frame readable)
        └──► Ghi bản ghi vào SQLite WAL qua hàng đợi DBWriteQueue an toàn
        │
        ▼
 [6. GIÁM THỊ XEM LẠI & DUYỆT SỰ CỐ]
        │
        ├──► Giám thị mở modal xem lại clip MP4 tại `/evidence/{incident_id}.mp4`
        └──► Nhấn "Xác nhận vi phạm" (`confirmed`) hoặc "Bỏ qua" (`dismissed`)
```

---

## 6. THUẬT NGỮ VÀ MÃ ĐỊNH DANH CHUẨN HÓA (STANDARDIZED TERMINOLOGY)

Để đảm bảo tính nhất quán trên toàn bộ giao diện, API, schema cơ sở dữ liệu và báo cáo, các thuật ngữ sau được định nghĩa cố định:

| Thuật ngữ chuẩn | Giải thích kỹ thuật | Phạm vi giá trị hợp lệ |
|---|---|---|
| `violation_type` | Loại hành vi vi phạm được nhận diện bởi mô hình AI | Duy nhất: `PHONE` hoặc `HEAD_TURNING` |
| `confidence` | Điểm tin cậy nhận diện mô hình hoặc điểm nghi vấn | Canonical runtime/storage: xác suất thô trong đoạn `[0.0, 1.0]`. Thang đo `(1.0, 100.0]` chỉ được chấp nhận tại tầng tương thích ngược (compatibility normalization path) cho dữ liệu legacy và tự động chia 100. Giá trị âm, `NaN`, `Inf` hoặc `> 100.0` bị từ chối. UI hiển thị phần trăm (`* 100`). *(Residual risk: giá trị lỗi như `2.0` có thể bị chuẩn hóa thành 0.02 tức 2% thay vì báo lỗi)* |
| `level` / `severity` | Mức độ cảnh báo của sự cố | Duy nhất: `yellow` (cảnh báo nghi vấn) hoặc `red` (vi phạm nghiêm trọng) |
| `status` | Trạng thái xử lý sự cố bởi giám thị | Duy nhất: `pending` (chờ duyệt), `confirmed` (đã xác nhận), `dismissed` (bỏ qua / cảnh báo giả) |
| `track_id` | Mã số theo dõi chuyển động ẩn danh tạm thời | Số nguyên không âm (`integer`), reset theo phiên |
| `source_id` | Định danh nguồn video đầu vào | Chuỗi ký tự chuẩn: `webcam_local`, `cam_01`, `demo_video` |
| `session_id` | Định danh phiên giám sát hiện tại | Chuỗi ký tự (UUID hoặc timestamp) cô lập trạng thái hoạt động |
| `pre_roll_seconds` | Thời lượng video lưu trữ trước thời điểm vi phạm | Mặc định: `5.0` giây |
| `post_roll_seconds` | Thời lượng video ghi nhận tiếp sau thời điểm vi phạm | Mặc định: `10.0` giây |
| `cooldown_seconds` | Thời gian chờ tối thiểu giữa 2 lần kích hoạt clip cùng đối tượng | Mặc định: `6.0` giây |
| `phone_confidence` | Ngưỡng xác suất phát hiện điện thoại của mô hình YOLO | Mặc định: `0.35` (raw probability 0.35, tương đương 35%) |
| `posture_alert_seconds` | Ngưỡng thời gian quay đầu liên tục để leo thang cờ Đỏ | Mặc định: `1.25` giây |
| `suspicion_threshold` | Ngưỡng điểm nghi vấn tư thế chuẩn hóa kích hoạt cờ Vàng | Mặc định: `0.50` (Normalized Posture Suspicion Score, không thứ nguyên, thang đo [0.0 - 1.0]; không phải góc) |

---

## 7. CÔNG BỐ CÁC KHÓA CHẶN KỸ THUẬT ĐỘC LẬP (INDEPENDENT TECHNICAL BLOCKERS)

Hệ thống ghi nhận minh bạch 3 khóa chặn kỹ thuật độc lập phục vụ công tác nghiệm thu và viết Báo cáo KHKT:

### 7.1. Blocker D-01: Training Dataset Lineage
- **Mã định danh:** `BLOCKER D-01`
- **Trạng thái trên workstream máy train (Sprint 2.2A):** `CLOSED`
- **Trạng thái trên repo chính hiện tại:** `CLOSED`
- **Bản chất:** Gói Pass 1.3 cung cấp đủ bằng chứng để tái dựng cấu hình huấn luyện lịch sử ở cấp artifact trong phạm vi được liệt kê (10 tệp canonical đã được nhập vào `reports/evidence/training_lineage/` và kiểm chứng toàn vẹn qua `scripts/verify_training_lineage_handoff.py`).
- **Các thông số kỹ thuật đã kiểm chứng được phép nhập:**
  - Tệp trọng số triển khai `phone_detector_v5.pt` có cùng SHA-256 (`23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2`, kích thước 19.245.082 bytes) với artifact `best.pt` được xác định trong run `phone_detector_v5` (đối chiếu đồng nhất artifact bằng SHA-256).
  - Dataset lịch sử `phone_merged` có 2.961 ảnh và 3.706 phone boxes (splits: 2.434 train, 382 validation, 145 internal test).
  - Kiến trúc mô hình: `YOLO11s`; siêu tham số run cuối: `imgsz=960`, `batch=6`, `optimizer=auto`, seed 0, `deterministic=True`, `close_mosaic=10`.
  - Lịch sử huấn luyện ghi nhận epoch 1–60; có dấu vết resume trước epoch 6 (thể hiện qua `args.yaml` model/resume và `results.csv` reset time tại epoch 6).
  - Các metric trong `results.csv` mang bản chất `TRAINING_VALIDATION_ONLY`.
  - Checkpoint tiền huấn luyện ban đầu (Initial pretrained checkpoint): `UNRESOLVED` (không khẳng định chắc chắn từ `yolo11s.pt`).
  - Epoch trực tiếp sinh ra `best.pt`: `UNRESOLVED` (không khẳng định epoch 55 là best epoch).
  - Kiểm tra rò rỉ: Không phát hiện exact-hash hoặc filename collision giữa các split; chưa kiểm tra toàn diện near-duplicate/session/subject leakage (không tuyên bố zero leakage).
  - Vai trò của MultiV và 11 video test: `external_challenge_previously_seen` (không đạt tiêu chuẩn untouched holdout).
- **Ràng buộc:** Các thông số huấn luyện cũ trong checkpoint `phone_detector_v5.pt` phải được ghi chú rõ là `TRAINING_VALIDATION_ONLY`.

### 7.2. Blocker D-02: Phone Independent Untouched Holdout Evaluation
- **Mã định danh:** `BLOCKER D-02`
- **Trạng thái:** `OPEN`
- **Bản chất:** D-02 được định nghĩa là tập đánh giá độc lập, chưa từng tham gia train, validation, điều chỉnh threshold hoặc kiểm thử thủ công trước đó, đồng thời đại diện hợp lý cho bối cảnh sử dụng dự kiến. OOD evaluation là một đánh giá bổ sung, tách biệt với D-02.
- **Ràng buộc:** Không tự bịa đặt hoặc công bố chỉ số độc lập trong Báo cáo KHKT cho đến khi có dữ liệu kiểm định thực tế nạp vào bộ harness `scripts/evaluation/`.

### 7.3. Blocker D-03: Head-Turning Ground-Truth Event Evaluation
- **Mã định danh:** `BLOCKER D-03`
- **Trạng thái:** `OPEN`
- **Bản chất:** Hệ thống chưa có tập dữ liệu video phòng thi thực tế được gán nhãn mốc thời gian vi phạm (event ground truth intervals) để benchmark độ chính xác định lượng (tIoU, Event F1-score, Onset Error) cho hành vi quay đầu / phân tích tư thế.
- **Ràng buộc:** Báo cáo KHKT chỉ mô tả giải thuật hình học kết hợp quy tắc thời gian thực (`>= 1.25s`) và kết quả kiểm thử synthetic; không công bố số liệu định lượng giả định.

---
**KẾT THÚC VĂN BẢN ĐẶC TẢ ĐÓNG BĂNG PHẠM VI HỆ THỐNG**
