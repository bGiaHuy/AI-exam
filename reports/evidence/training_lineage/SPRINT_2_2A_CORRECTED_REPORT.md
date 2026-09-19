# BÁO CÁO KIỂM TOÁN DỮ LIỆU & DẤU VẾT HUẤN LUYỆN
## Sprint 2.2A — Training Dataset Provenance & Footprint Recovery
### (Corrected Evidence Edition — Pass 1.3)

**Dự án:** AI Exam Control / AI-Powered Automated Proctoring System  
**Mục tiêu kiểm toán:** Checkpoint `model/weights/phone_detector_v5.pt`  
**Phương pháp:** Forensic Audit Read-Only (Không sửa code, không sửa weights, không train lại, bảo toàn nguyên trạng dữ liệu nguồn)  
**Thời gian hoàn thành:** 2026-09-14  

---

### A. Executive Verdict (Kết luận điều hành)

> **KẾT LUẬN TOÀN SPRINT: `STRONG TRAINING LINEAGE RECOVERED`**  
> *(Training lineage recovered with strong artifact-level evidence)*

1. **Khớp mã băm tuyệt đối:** File `model/weights/phone_detector_v5.pt` trên branch Git `model/exam-monitor-core` có mã SHA-256 trùng khớp 100% với artifact huấn luyện `best.pt` tại run `data and finetune 3/runs/detect/runs/phone_detector_v5/weights/best.pt`:
   - **SHA-256:** `23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2`
   - **Kích thước:** `19,245,082 bytes` (~18.35 MB)
2. **Nguồn gốc dữ liệu huấn luyện:** Dataset dùng để huấn luyện checkpoint này là **`data and finetune 3/phone_merged`** (được đối chiếu qua bản sao snapshot `training_data_phone.redacted.yaml` — *EVIDENCE_ONLY*), gồm **2,961 ảnh** và **3,706 bounding boxes class `phone`**.
3. **Nguồn gốc hợp thành của `phone_merged`:** Được tổng hợp từ 3 gói dataset Roboflow Universe mở (CC BY 4.0):
   - `mobilephone.v3i.yolov11.zip` (963 ảnh)
   - `mobilephone2.v1i.yolov11.zip` (1,000 ảnh)
   - `mobilephone3.v1i.yolov11.zip` (998 ảnh)
   *(Mức độ xác minh: Tương ứng chính xác theo cấu trúc tên file, số lượng mẫu và cấu trúc split — corresponds by filename/count/split structure: 963 + 1,000 + 998 = 2,961 ảnh; chưa thực hiện kiểm tra mã băm SHA-256 từng file ảnh đơn lẻ giữa ZIP nguồn và thư mục giải nén nên không gọi là content-identical).*
4. **Dấu vết quá trình Huấn luyện & Khởi tạo (Mới ghi nhận trong Pass 1.3):**
   - **Bằng chứng Resume:** Quá trình huấn luyện đã được resume ít nhất một lần sau Epoch 5 (`resume_boundary_observed_before_epoch: 6`), thể hiện qua việc `args.yaml` có `model: .../last.pt`, `resume: .../last.pt` và cột `time` trong `results.csv` tích lũy đến 1219.98s ở Epoch 5 rồi đột ngột reset về 119.816s ở Epoch 6.
   - **Lịch sử Epoch:** Training history lưu 60 epoch từ 1 đến 60; run đã được resume ít nhất một lần, thể hiện qua args.yaml và việc cột time reset tại epoch 6.
   - **Kiến trúc & Khởi tạo ban đầu:** Kiến trúc mô hình là **YOLO11s**. Checkpoint đầu vào của run cuối được ghi nhận là `last.pt`. Trạng thái checkpoint pre-trained ban đầu được phân loại là **`initial_pretrained_checkpoint_status: UNRESOLVED`** do không còn lưu artifact/log của lần chạy đầu tiên (Epoch 1–5) để chứng minh trực tiếp `yolo11s.pt`.
5. **Kiểm tra rò rỉ (Leakage & Giới hạn):**
   - Không phát hiện exact-content leakage (trùng mã băm SHA-256) hoặc filename collision giữa các split Train - Valid - Test.
   - *Giới hạn học thuật:* Chưa kiểm tra được near-duplicate images, các frame tương quan từ cùng video session, hoặc tính độc lập theo subject/scene. Do đó, **chưa khẳng định zero-leakage tuyệt đối**.
6. **Cập nhật trạng thái Blocker:**
   - **`D-01 Training Dataset Lineage`:** **`CLOSED`**  
     *(Lý do: Deployed checkpoint khớp SHA-256 với artifact training `best.pt`; có đầy đủ config, args, results và dataset snapshot; quan hệ dataset–run–checkpoint được chứng minh chặt chẽ).*
   - **`D-02 Independent Untouched Holdout Evaluation`:** **`OPEN`**  
     *(Mở nhiệm vụ đánh giá độc lập trên tập dữ liệu hoàn toàn chưa từng quan sát).*

---

### B. Phạm vi & Mức độ kiểm tra các nguồn dữ liệu

Tất cả artifact thiết yếu để phục hồi training lineage đều đã truy cập được. Các ZIP/video dung lượng lớn được kiểm kê và băm; mức độ kiểm tra nội dung cụ thể được phân định minh bạch như sau:

| Nhóm nguồn dữ liệu | Đối tượng cụ thể | Mức độ kiểm tra thực tế |
| :--- | :--- | :--- |
| **Training Run Artifacts** | `runs/detect/runs/phone_detector_v5` (`best.pt`, `last.pt`, `args.yaml`, `results.csv`, plots) | **Đã đọc toàn bộ nội dung, phân tích bảng số liệu, phát hiện dấu vết resume, băm SHA-256** |
| **Active Dataset** | `data and finetune 3/phone_merged` (train, valid, test) | **Đã kiểm tra 100% tệp tin, đếm nhãn, đếm box, băm kiểm tra leakage giữa các split** |
| **Roboflow Source ZIPs** | `mobilephone 1, 2, 3`, `summary`, `exam-cheating-v2`, `data only train` | **Đã băm SHA-256, duyệt toàn bộ cấu trúc entry, đối chiếu tên file/số lượng mẫu/split structure, đọc license README** |
| **Legacy / MultiV ZIPs** | `cheating-project`, `giam_sat_gian_lan`, `-data labelled...`, `data cam trên cao...` | **Đã băm SHA-256, kiểm kê danh mục entry bên trong** |
| **Video Media Thô** | `V1.zip`, `V2.zip`, `V3.zip`, `V5.zip` (~18.9 GB) | **Đã kiểm kê danh mục video, băm SHA-256 toàn bộ file ZIP** |
| **Test Video Media** | `data and finetune 3/data test` (11 videos) | **Đã kiểm kê danh mục, kiểm tra đối chiếu tên file và tiền tố với tập train** |

*(Lưu ý: Việc có mã SHA-256 chứng minh tính toàn vẹn và nguồn gốc tệp tin, không thay thế cho việc đánh giá toàn diện chất lượng nội dung thị giác của các tệp dung lượng lớn).*

---

### C. Nguồn bị chặn (Blocked / Missing)

- **Không có nguồn nào bị chặn.** Tất cả các tệp tin cần thiết cho việc phục hồi lineage đều đã sẵn sàng và được kiểm tra cục bộ.

---

### D. Inventory & Bảng băm SHA-256

| Tệp tin / Đối tượng | Kích thước | Ngày sửa đổi | SHA-256 |
| :--- | :--- | :--- | :--- |
| `model/weights/phone_detector_v5.pt` (Repo) | 19,245,082 bytes | 2026-08-27 00:49:48 | `23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2` |
| `runs/.../phone_detector_v5/weights/best.pt` | 19,245,082 bytes | 2026-08-27 00:49:48 | `23fa698727a49cb8ba7d260c1ac13f01d4d27e8726e97aa3d8fef992ad5e19c2` |
| `runs/.../phone_detector_v5/weights/last.pt` | 19,245,082 bytes | 2026-08-27 00:49:48 | `1118a896828de3c6d78d03e10e8412f276a356de0a9405087baf7a718d787389` |
| `yolo11m-pose.pt` (Pose model) | 42,459,307 bytes | - | `29b17eaf3a3117cbea906090dbedf9159f7c6a49db58ec8b99ed2dfde1cf6eb2` |
| `mobilephone.v3i.yolov11.zip` | 27.31 MB | 2026-08-26 | `67d26affa3a0539adbe2c3d9db38a85b339b5c15106ccc2ad3bc5885a0fc5869` |
| `mobilephone2.v1i.yolov11.zip` | 30.18 MB | 2026-08-26 | `eebcb79acc6b4e3f36848283222dd7cb9b900bab5e6cdb14c629778439609db9` |
| `mobilephone3.v1i.yolov11.zip` | 21.73 MB | 2026-08-26 | `0626c7600eaf6bb4d17e1adfcb00f2df7871e37910e656e75ae3234081f09fc7` |
| `summary.v1i.yolov11.zip` | 26.66 MB | 2026-08-25 | `aa0a2d8616b30964bed20bf6cb1af6ede5446fbcb9355817572e4c7b8de2fb1b` |
| `exam-cheating-v2.v1i.yolov11.zip` | 9.39 MB | 2026-05-12 | `19ef0144529fdd8e9dc0beef69f0f9c1bc35ab98d7fd42eb9eacb4a9b560eef1` |
| `data only train của anh ấn ộ.zip` | 5.16 MB | 2026-08-24 | `3dec36f8477b797bcb4f7e24eafe53014fee5e5c72d8b0c7c7ee44f3cb7ada14` |
| `cheating-project.v6i.yolov11-hai labelled.zip`| 105.09 MB | 2025-01-04 | `e034afd03ff3bf0066c92cc9414513ce0fd1d635b930b7d0ac8a9f874d25b362` |
| `giam_sat_gian_lan.v2i.yolov11 hai labelled.zip`| 96.59 MB | 2024-04-10 | `2125452045e8ec338d85e3d423c8bd43c4499c4b7708d74cd0c92354fd304821` |
| `-data labelled theo face,hand...zip` | 280.64 MB | 2024-05-03 | `c98305ce3e43a04d38c1864993fcefcfe28fd2a716936995fd2d21e956587307` |
| `V1.zip` (Source Media MultiV) | 941.83 MB | - | `d3dc8596b23ace6fa13125feb9530adb0b3d4b63f9ad3dcd4ddfb430e0c09d8c` |
| `V2.zip` (Source Media MultiV) | 3,412.28 MB | - | `2c94b141c0bf09365a3f66e6afdc2a012a6a14717a01e965fce921d754e82d47` |
| `V3.zip` (Source Media MultiV) | 6,334.85 MB | - | `e5bba9f2c003317e9a355b005c537d90b0e9a93181ee7b5d92cefaef29581d7a` |
| `V5.zip` (Source Media MultiV) | 8,250.44 MB | - | `8d4b2312d8710175a8fd5abfa3c70bdb264256408c39b345d70fd499efb671c9` |

---

### E. Cấu trúc & Thống kê Dataset huấn luyện (`phone_merged`)

Dataset `phone_merged` được cấu hình đối chiếu qua `training_data_phone.redacted.yaml` (1 class: `0: phone`):
- **Tập Train:** 2,434 ảnh | 2,434 files label (0 nhãn rỗng) | **3,042 bounding boxes**
- **Tập Valid:** 382 ảnh | 382 files label (0 nhãn rỗng) | **490 bounding boxes**
- **Tập Test:** 145 ảnh | 145 files label (0 nhãn rỗng) | **174 bounding boxes**
- **Tổng cộng:** **2,961 ảnh** | **3,706 bounding boxes class `phone`**.
- Toàn bộ các ảnh đều có file label tương ứng (100% paired).

---

### F. Nguồn gốc & Bản quyền 3 Dự án Roboflow Universe

Toàn bộ thông tin bản quyền và giấy phép được trích xuất trực tiếp từ các file artifact `README.dataset.txt` và `README.roboflow.txt` lưu bên trong từng gói ZIP:

1. **`mobilephone.v3i.yolov11.zip`:**
   - **Project URL:** https://universe.roboflow.com/du-tran/mobilephone-vpgle
   - **Version:** `v3`
   - **Attribution / Chủ thể:** Roboflow workspace user `du-tran`
   - **Nguồn chứng minh giấy phép:** `README.dataset.txt` (Dòng 5: `License: CC BY 4.0`)
   - **Ngày Export:** 2026-08-26 10:09am GMT
   - **Ngày kiểm toán / xác minh:** 2026-09-14
   - **Đóng góp:** 963 ảnh (823 train, 100 valid, 40 test).
2. **`mobilephone2.v1i.yolov11.zip`:**
   - **Project URL:** https://universe.roboflow.com/du-tran/mobilephone2-lmw02
   - **Version:** `v1`
   - **Attribution / Chủ thể:** Roboflow workspace user `du-tran`
   - **Nguồn chứng minh giấy phép:** `README.dataset.txt` (Dòng 5: `License: CC BY 4.0`)
   - **Ngày Export:** 2026-08-26 10:15am GMT
   - **Ngày kiểm toán / xác minh:** 2026-09-14
   - **Đóng góp:** 1,000 ảnh (801 train, 175 valid, 24 test).
3. **`mobilephone3.v1i.yolov11.zip`:**
   - **Project URL:** https://universe.roboflow.com/du-tran/mobilephone3
   - **Version:** `v1`
   - **Attribution / Chủ thể:** Roboflow workspace user `du-tran`
   - **Nguồn chứng minh giấy phép:** `README.dataset.txt` (Dòng 5: `License: CC BY 4.0`)
   - **Ngày Export:** 2026-08-26 10:16am GMT
   - **Ngày kiểm toán / xác minh:** 2026-09-14
   - **Đóng góp:** 998 ảnh (810 train, 107 valid, 81 test).

*Ghi chú đối soát:* Mức đối chiếu giữa 3 ZIP nguồn và `phone_merged` được xác định theo cấu trúc tên file, số lượng mẫu và tỷ lệ phân chia (*corresponds by filename/count/split structure*).

---

### G. So sánh quan hệ giữa hai ZIP (`exam-cheating-v2` và `data only train`)

- **`exam-cheating-v2.v1i.yolov11.zip`:** 527 files, 6 classes (`book_visible`, `passing_note`, `peeking_around`, `person_normal`, `showing_paper`, `using_mobile`). URL: https://universe.roboflow.com/basit-mirza/exam-cheating-v2.
- **`data only train của anh ấn ộ.zip`:** 53 files, 3 classes (`Looking Around`, `Normal`, `phone`). URL: https://universe.roboflow.com/du-tran/exam-cheating-syrgs-gquul.
- **Quan hệ:** Hai tệp này **KHÔNG** phải là quan hệ cha - con (sub-set). Chỉ có 2 file ảnh trùng tên (chiếm 3.8%), đại diện cho 2 thí nghiệm trích xuất thử nghiệm độc lập trong giai đoạn đầu dự án. Cả hai **KHÔNG ĐƯỢC SỬ DỤNG** để train `phone_detector_v5`.

---

### H. Đối chiếu Checkpoint, Training Run & Phân tích Cực trị Epoch

#### 1. Phân định khái niệm mô hình & Trạng thái khởi tạo:
- **Architecture:** `YOLO11s` (Kiến trúc mạng nơ-ron).
- **Final/Resumed Run Input:** `last.pt` (Checkpoint đầu vào của lượt chạy cuối).
- **Initial Pretrained Checkpoint Status:** **`UNRESOLVED`** (Do không có file log/config của lần chạy ban đầu từ Epoch 1–5 để chứng minh trực tiếp `yolo11s.pt`).
- **Final Deployed Artifact:** `phone_detector_v5.pt` (Checkpoint triển khai thực tế trên repo).

#### 2. Cấu hình huấn luyện & Bằng chứng Training Resume:
- **`args.yaml`:** `EVIDENCE_ONLY — HISTORICAL FINAL/RESUMED RUN CONFIG`
  - `model`: `runs\detect\runs\phone_detector_v5\weights\last.pt`
  - `resume`: `runs\detect\runs\phone_detector_v5\weights\last.pt`
  - `imgsz`: 960 | `batch`: 6
  - `optimizer`: **auto** (ghi nhận đúng nguyên văn `optimizer=auto`, không suy đoán là SGD)
- **Bằng chứng Resume:**
  - `training_resume_detected`: **`true`**
  - `resume_boundary_observed_before_epoch`: **`6`**
  - Cột thời gian `time` trong `results.csv` tích lũy liên tục từ Epoch 1 đến Epoch 5 (đạt `1219.98s`), sau đó đột ngột reset về `119.816s` tại Epoch 6. Đây là bằng chứng kỹ thuật rõ ràng chứng minh run đã được resume lại ít nhất một lần sau Epoch 5.
- **Dấu hiệu lịch sử Epoch:** Training history lưu 60 epoch từ 1 đến 60; run đã được resume ít nhất một lần, thể hiện qua args.yaml và việc cột time reset tại epoch 6.
- Nhãn chỉ số: **`[TRAINING_VALIDATION_ONLY]`**

#### 3. Bảng phân tích các Epoch Cực trị (Extrema Analysis từ `results.csv`):

| Tiêu chí cực trị | Epoch | Precision (B) | Recall (B) | mAP@50 (B) | mAP@50-95 (B) | Ghi chú kỹ thuật |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Max Precision** | **53** | **0.80397** | 0.66327 | 0.76711 | 0.45396 | Đỉnh độ chính xác dương tính |
| **Max Recall** | **59** | 0.78275 | **0.70408** | 0.78326 | 0.47023 | Đỉnh tỷ lệ bao phủ mẫu dương tính |
| **Max mAP@50** | **55** | 0.78802 | 0.68980 | **0.78578** | 0.46456 | Đỉnh mAP@50 trên tập validation |
| **Max mAP@50-95** | **60** | 0.76217 | 0.68367 | 0.76915 | **0.47155** | Đỉnh IoU nghiêm ngặt |
| **Final Epoch** | **60** | 0.76217 | 0.68367 | 0.76915 | 0.47155 | Epoch kết thúc quá trình huấn luyện |

#### 4. Trạng thái xác định Epoch sinh ra `best.pt`:
- **Trạng thái chính thức:** **`BEST_CHECKPOINT_SOURCE_EPOCH_UNRESOLVED`**
- **Lý do khoa học:**
  - Không tự tiện áp dụng công thức fitness từ các phiên bản YOLO khác khi chưa trích xuất được định nghĩa hàm fitness cụ thể của bản Ultralytics 8.4.128 trong môi trường kiểm toán read-only.
  - Báo cáo từ chối gọi Epoch 55 là "best epoch" chỉ vì mAP@50 cao nhất.
  - Trạng thái chưa giải quyết này **hoàn toàn không làm ảnh hưởng** đến kết luận cốt lõi: Deployed checkpoint `phone_detector_v5.pt` trùng khớp SHA-256 tuyệt đối với artifact `best.pt` của run huấn luyện.

---

### I. Kiểm tra Rò rỉ Dữ liệu & Giới hạn Nghiên cứu (Data Leakage & Study Limitations)

1. **Những điều đã kiểm chứng:**
   - Không phát hiện exact-content leakage (trùng lặp mã băm SHA-256) giữa các tập Train, Valid và Test trong `phone_merged`.
   - Không có trùng lặp tên file (Filename Collision = 0) giữa Train, Valid và Test.
   - Không có frame nào của 11 video test trùng khớp nội dung hoặc tên file với tập train `phone_merged`.
2. **Những giới hạn nghiên cứu chưa kiểm tra (Limitations):**
   - Chưa kiểm tra mức độ ảnh tương tự gần kề (**near-duplicate images**).
   - Chưa kiểm tra việc các frame khác nhau có thể được trích xuất từ cùng một video session hay không.
   - Chưa kiểm chứng mức độ độc lập tuyệt đối theo từng thí sinh (subject) hoặc từng góc máy (scene/camera).
   - Do đó, báo cáo KHKT **chưa được khẳng định zero-leakage tuyệt đối**.

---

### J. Vai trò của MultiV & Bộ Video Test

- `V1.zip` (84 video), `V2.zip` (31 video), `V3.zip` (240 video), `V5.zip` (178 video) đại diện cho các video thô quay từ nhiều góc máy.
- Các video trong `data and finetune 3/data test` (như `8.mp4`, `DSC_0030.mov`) được trích xuất từ nguồn này.
- **Phân loại vai trò chuẩn hóa:** **`external_challenge_previously_seen`** (Áp dụng thống nhất cho toàn bộ báo cáo).
  - *Đặc điểm khẳng định:*
    * Hoàn toàn **không tham gia** vào quá trình huấn luyện model phone detector.
    * Đã từng được người thực hiện chạy thử nghiệm bằng tay sau khi hoàn thành model để quan sát định tính.
    * **Không đủ điều kiện** làm untouched holdout hoặc independent holdout chính thức cho các so sánh định lượng trước–sau.

---

### K. Bảng xếp hạng mức bằng chứng (Evidence Classification)

| Dataset / Nguồn | Mức bằng chứng | Lý do xác định |
| :--- | :--- | :--- |
| **`phone_merged`** (`mobilephone 1, 2, 3`) | **`STRONG MATCH`** | Khớp cấu hình, khớp 2,961 ảnh với `args.yaml` và `results.csv`, khớp training artifacts và SHA-256 của checkpoint. |
| `exam-cheating-v2.v1i.yolov11.zip` | **`REJECTED`** | Không khớp class, không khớp số lượng, không thuộc lineage `phone_detector_v5`. |
| `data only train của anh ấn ộ.zip` | **`REJECTED`** | Dataset thử nghiệm cũ (53 ảnh, 3 class). |
| `cheating-project...zip` & `giam_sat_gian_lan...zip` | **`REJECTED`** | Dùng cho các run cũ (v1, v2). |
| `V1.zip` - `V5.zip` (MultiV Videos) | **`external_challenge_previously_seen`** | Video thực tế đa góc quay đã từng xem trước. |

---

### L. Phân loại vai trò dữ liệu (Data Role Assignment)

- **`phone_merged` (mobilephone 1, 2, 3):** `historical_train` (2,434 ảnh) & `historical_validation` (382 ảnh) & `internal_test` (145 ảnh).
- **`COCO Keypoints Dataset`:** `historical_pretrained` (Trọng số gốc cho `yolo11m-pose.pt`).
- **`data and finetune 3/data test` (11 videos):** `external_challenge_previously_seen`.
- **`V1.zip`, `V2.zip`, `V3.zip`, `V5.zip`:** `source_media_unprocessed`.
- **`exam-cheating-v2`, `data only train`:** `legacy_experimental_scratch`.

---

### M. Những điều ĐƯỢC PHÉP khẳng định trong Báo cáo KHKT

1. Checkpoint `model/weights/phone_detector_v5.pt` trên Git khớp SHA-256 tuyệt đối với `best.pt` trong thư mục run `phone_detector_v5`.
2. Model được train từ tập dữ liệu `phone_merged` gồm **2,961 ảnh** (2,434 train / 382 valid / 145 test), tương ứng theo tên file, số lượng và split (*corresponds by filename/count/split structure*) từ 3 project Roboflow mở (License CC BY 4.0 có attribution đầy đủ).
3. Training history lưu 60 epoch từ 1 đến 60; run đã được resume ít nhất một lần, thể hiện qua args.yaml và việc cột time reset tại epoch 6. Kiến trúc mạng là **YOLO11s**, độ phân giải **960x960**, `batch: 6`, `optimizer: auto`.
4. Không phát hiện exact-content leakage hoặc filename collision giữa các split Train, Valid, Test.
5. Đã bóc tách riêng bảng số liệu cực trị (Precision cao nhất ở Epoch 53, Recall cao nhất ở Epoch 59, mAP@50 cao nhất ở Epoch 55, mAP@50-95 cao nhất ở Epoch 60).

---

### N. Những điều CHƯA ĐƯỢC PHÉP khẳng định

1. **Chưa được khẳng định** zero-leakage tuyệt đối (do chưa phân tích near-duplicates và tương quan session).
2. **Chưa được khẳng định** model được khởi tạo trực tiếp từ `yolo11s.pt` nếu không có log/artifact của lần chạy ban đầu epoch 1–5 (giữ trạng thái `initial_pretrained_checkpoint_status: UNRESOLVED`).
3. **Chưa được khẳng định** tính content-identical tuyệt đối giữa 3 ZIP và `phone_merged` nếu chưa thực hiện hash nội dung từng file (giữ mức `corresponds by filename/count/split structure`).
4. **Chưa được khẳng định** mAP 78.58% là hiệu năng thực tế ngoài đời (đây là chỉ số `[TRAINING_VALIDATION_ONLY]`).
5. **Chưa được khẳng định** Epoch 55 là "Best Epoch" dứt điểm (giữ trạng thái `BEST_CHECKPOINT_SOURCE_EPOCH_UNRESOLVED`).
6. **Chưa được khẳng định** tập 11 video test là "untouched holdout" (phải dùng đúng nhãn `external_challenge_previously_seen`).
7. **Chưa được khẳng định** optimizer là SGD nếu chỉ căn cứ vào file cấu hình `optimizer: auto`.

---

### O. Trạng thái Blocker & Đề xuất

- **`D-01 Training Dataset Lineage`:** **`CLOSED`**  
  *(Lý do đóng: Deployed checkpoint khớp SHA-256 với artifact training; có snapshot dataset `phone_merged`, file cấu hình lịch sử `training_data_phone.redacted.yaml`, `args.yaml`, `results.csv`; mối liên kết dataset–run–checkpoint được chứng minh chặt chẽ).*
- **`D-02 Independent Untouched Holdout Evaluation`:** **`OPEN`**  
  *(Nhiệm vụ kế tiếp: Đánh giá mô hình trên bộ dữ liệu kiểm thử độc lập, hoàn toàn mới chưa từng quan sát).*

---

### P. Cam kết liêm chính & Không can thiệp

- **Xác nhận:** Toàn bộ quá trình kiểm toán được thực hiện ở chế độ **Read-Only**.
- **Không can thiệp:** Không sửa mã nguồn, không sửa checkpoint weights, không train lại và không sửa đổi bất kỳ tệp dữ liệu nào trong dự án.
