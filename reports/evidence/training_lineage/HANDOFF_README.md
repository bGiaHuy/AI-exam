# 📦 Sprint 2.2A Evidence Handoff Package
## Training Dataset Provenance & Footprint Recovery
### (Corrected Evidence Edition — Pass 1.3)

Thư mục này chứa toàn bộ tài liệu và artifact nhỏ phục vụ bàn giao và nghiệm thu **Sprint 2.2A** của dự án AI Exam Control sang repository chính.

---

### 📂 Danh mục tệp tin trong gói bàn giao:

1. **`SPRINT_2_2A_CORRECTED_REPORT.md`**: Toàn văn Báo cáo Kiểm toán dữ liệu (Phiên bản Corrected Evidence Edition - Pass 1.3).
2. **`lineage_manifest.json`**: Tập tin manifest có cấu trúc chứa toàn bộ thông số, metadata, băm SHA-256, và trạng thái phục hồi lineage.
3. **`training_data_phone.redacted.yaml`**: `EVIDENCE_ONLY — NOT AN EXECUTABLE DATASET CONFIG` (Bản sao cấu hình dataset lịch sử phục vụ đối soát bằng chứng, đã redact đường dẫn cá nhân, không dùng để chạy trực tiếp trên repo chính. File cấu hình thực thi nằm tại `datasets/phone/data_phone.yaml`).
4. **`args.yaml`**: `EVIDENCE_ONLY — HISTORICAL FINAL/RESUMED RUN CONFIG` (Bản sao cấu hình siêu tham số của run huấn luyện/resumed cuối cùng).
5. **`results.csv`**: Bản sao nhật ký huấn luyện 60 epoch trích xuất từ run `phone_detector_v5`.
6. **`README_mobilephone_v3.txt`**: Metadata, URL và giấy phép CC BY 4.0 của gói dữ liệu Roboflow 1.
7. **`README_mobilephone2_v1.txt`**: Metadata, URL và giấy phép CC BY 4.0 của gói dữ liệu Roboflow 2.
8. **`README_mobilephone3_v1.txt`**: Metadata, URL và giấy phép CC BY 4.0 của gói dữ liệu Roboflow 3.
9. **`artifact_hashes.csv`**: Danh sách mã băm SHA-256 của từng tệp tin trong gói bàn giao này để kiểm tra tính toàn vẹn.

---

### 🔍 Ghi nhận dấu vết kỹ thuật & Giới hạn bằng chứng (Pass 1.3):

1. **Bằng chứng Quá trình Huấn luyện được Resume:**
   - `args.yaml` ghi nhận `model: runs\detect\runs\phone_detector_v5\weights\last.pt` và `resume: runs\detect\runs\phone_detector_v5\weights\last.pt`.
   - `results.csv` ghi nhận cột thời gian `time` tích lũy đến `1219.98s` ở Epoch 5 và đột ngột reset về `119.816s` ở Epoch 6.
   - **Kết luận:** Quá trình huấn luyện đã được resume ít nhất một lần sau Epoch 5 (`resume_boundary_observed_before_epoch: 6`).
2. **Trạng thái Khởi tạo Checkpoint ban đầu:**
   - **Kiến trúc:** `YOLO11s`
   - **Input của Run cuối (Resumed run):** `last.pt`
   - **Trạng thái Pretrained ban đầu:** `initial_pretrained_checkpoint_status: UNRESOLVED` (Do không có file log/config của lần chạy ban đầu từ Epoch 1–5 để chứng minh trực tiếp `yolo11s.pt`).
   - **Dấu hiệu Epoch:** Training history lưu 60 epoch từ 1 đến 60; run đã được resume ít nhất một lần, thể hiện qua args.yaml và việc cột time reset tại epoch 6.
3. **Mức độ đối chiếu 3 gói Roboflow nguồn với `phone_merged`:**
   - Khớp theo tên file, số lượng mẫu và cấu trúc phân chia (*corresponds by filename/count/split structure*: 963 + 1,000 + 998 = 2,961 ảnh).
   - Chưa thực hiện kiểm tra mã băm SHA-256 từng file ảnh đơn lẻ giữa ZIP nguồn và thư mục giải nén nên không gọi là content-identical tuyệt đối.
4. **Trạng thái các Blocker:**
   - `D-01 Training Dataset Lineage`: **CLOSED** (Lineage phục hồi vững chắc ở cấp độ artifact).
   - `D-02 Independent Untouched Holdout Evaluation`: **OPEN** (Cần thực hiện trên tập holdout độc lập).
   - Checkpoint source epoch: **`BEST_CHECKPOINT_SOURCE_EPOCH_UNRESOLVED`**.
   - Bộ 11 video test: **`external_challenge_previously_seen`**.

---

### 🛡️ Cam kết nội dung:
- **KHÔNG CHỨA:** Tệp tin ảnh, video hay file trọng số `.pt` lớn.
- **DUNG LƯỢNG:** Toàn bộ gói bàn giao dưới **100 KB**.
- **TÍNH TOÀN VẸN:** Đối chiếu mã băm trong `artifact_hashes.csv` trước khi tích hợp vào repository chính.
