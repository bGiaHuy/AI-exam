# BÁO CÁO KIỂM TOÁN VÀ NGHIỆM THU HỒ SƠ DỰ ÁN (FINAL DOCUMENT AUDIT)
### Dự án: Hệ Thống Hỗ Trợ Giám Sát Phòng Thi Bằng Thị Giác Máy Tính & Trích Xuất Video Bằng Chứng
### Hồ sơ dự thi KHKT Hà Nội — Đơn vị: Nhóm nghiên cứu

---

## 1. KẾT LUẬN KIỂM TOÁN CUỐI CÙNG (FINAL AUDIT VERDICT)

### **TRẠNG THÁI: READY_PENDING_METADATA_WITH_RECORDED_DB_DEVIATION**

> **Căn cứ kết luận:**
> 1. Toàn bộ nội dung kỹ thuật, kiến trúc hai luồng, mã nguồn, bộ kiểm thử tự động, giao diện chạy cục bộ và sơ đồ khoa học đã được đối chiếu và thống nhất xuyên suốt tất cả các tài liệu.
> 2. Đã áp dụng đầy đủ bộ quy chuẩn định dạng tài liệu tiếng Việt chuyên nghiệp từ kỹ năng `vietnamese-docs-style` (commit `d5e47b7`, profile `academic`). Cả hai tài liệu DOCX đạt kết quả **0 ERRORS** (Exit code 0) khi kiểm tra cấu trúc tự động qua công cụ `validate_docx.py`.
> 3. Đã loại bỏ các tuyên bố quá mức, thống nhất danh mục **7 chức năng cốt lõi (F-01 đến F-07)**, phân loại rành mạch ảnh giao diện chạy cục bộ (Nhóm A) và sơ đồ kỹ thuật (Nhóm B).
> 4. Phạm vi camera được thống nhất là **hệ thống hai camera (Dual-Camera)**. Nghiệm thu đồng thời hai camera vật lý ở trạng thái **HARDWARE ACCEPTANCE PENDING** (ba ô hiển thị trên giao diện kiểm thử thực chất là 01 webcam vật lý kết hợp 02 luồng kiểm thử phần mềm; không suy diễn giao diện ba ô thành hệ thống ba camera vật lý).
> 5. Ghi nhận tình trạng cơ sở dữ liệu: Trong phiên chạy live backend để chụp ảnh màn hình ngày 25/09/2026, cơ sở dữ liệu `cheating_system.db` đã ghi nhận thêm 14 bản ghi sự cố thật (tổng số bản ghi tăng từ 425 lên 439). Theo quy định an toàn dữ liệu, hệ thống không tự ý xóa hay rollback; tình trạng này được ghi nhận minh bạch trong báo cáo kiểm toán này và phản ánh vào tên trạng thái `WITH_RECORDED_DB_DEVIATION`. Không phát sinh thêm bất kỳ thay đổi nào vào CSDL trong vòng hoàn thiện tài liệu này.
> 6. Hồ sơ chờ bổ sung 3 trường siêu dữ liệu thí sinh trước khi in nộp chính thức:
>    - `[Tên trường THPT — Thí sinh bổ sung trước khi in nộp]`
>    - `[Họ và tên thí sinh 1 & Thí sinh 2 — Thí sinh bổ sung]`
>    - `[Họ và tên giáo viên hướng dẫn — Thí sinh bổ sung]`

---

## 2. BẰNG CHỨNG ÁP DỤNG KỸ NĂNG VIETNAMESE-DOCS-STYLE

### 2.1. Nguồn kỹ năng và Phiên bản thực tế
- **URL Repository:** `https://github.com/bGiaHuy/vietnamese-docs-style`
- **Thư mục tích hợp cục bộ:** `tools/vietnamese-docs-style/`
- **Commit / Version thực tế:** `d5e47b7` (nhánh `main`)
- **Profile được chọn:** `academic` (Báo cáo nghiên cứu khoa học / Khóa luận học thuật)
- **Về profile custom:** Do profile `custom` trong kỹ năng không bổ sung thêm quy tắc kiểm tra nào so với `academic` (profile `academic` áp dụng đầy đủ ràng buộc khổ giấy A4, căn lề, màu chữ đen và placeholder), việc tài liệu vượt qua `academic` với 0 lỗi đã bảo đảm đầy đủ tiêu chuẩn kỹ thuật.

### 2.2. Tài liệu hướng dẫn chuyên ngành đã nghiên cứu và vận dụng
Nhóm nghiên cứu đã nghiên cứu và vận dụng toàn bộ 6 tài liệu hướng dẫn chuẩn mực của skill:
1. `SKILL.md`: Tổng quan kỹ năng, kiểm soát phông chữ và OpenXML.
2. `references/document-profiles.md`: Ma trận phân cấp profile tài liệu. Thứ tự ưu tiên: Yêu cầu trực tiếp của người dùng $\rightarrow$ Quy chế cuộc thi KHKT $\rightarrow$ Báo cáo KHKT gốc $\rightarrow$ Profile Academic của skill $\rightarrow$ NĐ30 chỉ cho thành phần hành chính thuần túy.
3. `references/academic-report.md`: Hướng dẫn chuyên sâu cho Báo cáo KHKT: Bố cục La Mã (I, II, III...), cấu trúc tiểu mục số học (1, 1.1, 1.1.1), quy chuẩn trang bìa học thuật, danh mục bảng biểu - hình vẽ, mục lục, bảng chú giải thuật ngữ và tài liệu tham khảo chuẩn APA.
4. `references/editorial-quality-vi.md`: Tiêu chuẩn biên tập tiếng Việt: Quy chuẩn dấu câu, khoảng trắng đơn, quy tắc viết hoa, định dạng số thập phân kiểu Việt Nam (dấu phẩy cho phần thập phân, dấu chấm cho phần nghìn).
5. `references/style-spec.md`: Quy chuẩn thông số kỹ thuật Word/DOCX: Khổ giấy A4 Portrait ($21.0 \times 29.7$ cm), căn lề 4 chiều chuẩn mực (Trái 3.0cm, Phải 1.5-2.0cm, Trên 2.0cm, Dưới 2.0cm), phông chữ Times New Roman duy nhất, màu chữ chính được đặt RGB(0,0,0).
6. `references/validation-checklist.md`: Danh mục kiểm tra 4 bước trước khi nghiệm thu tài liệu (Page Setup, Text Formatting, Table Setup, Visual Structure).

### 2.3. Lệnh Build, Validate và Báo cáo Kết quả Lưu trữ
- Lệnh build:
  - `python scripts/build_bao_cao_khkt.py`
  - `python scripts/build_nhat_ky.py`
- Lệnh kiểm định tự động:
  - `python -X utf8 tools/vietnamese-docs-style/scripts/validate_docx.py deliverables/ha_noi/BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx --profile academic` $\rightarrow$ **Exit code 0 (Passed)**
  - `python -X utf8 tools/vietnamese-docs-style/scripts/validate_docx.py deliverables/ha_noi/NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx --profile academic` $\rightarrow$ **Exit code 0 (Passed)**
- Tệp lưu toàn bộ stdout/exit code: `deliverables/ha_noi/validation_report_academic.txt`.

### 2.4. Các Quy tắc của Skill đã Định hình Dàn trang Tài liệu
1. **Khổ giấy và Căn lề chuẩn A4:** Toàn bộ hai tài liệu DOCX được định dạng khổ giấy A4 Portrait ($21.0 \times 29.7$ cm), căn lề: Trái $30$ mm ($3.0$ cm), Phải $20$ mm ($2.0$ cm), Trên $20$ mm ($2.0$ cm), Dưới $20$ mm ($2.0$ cm).
2. **Kiểm soát Màu sắc Đơn sắc:** Màu chữ chính được đặt RGB(0,0,0). Toàn bộ văn bản, tiêu đề, số trang, đầu mục, chú thích hình/bảng đều dùng phông chữ Times New Roman.
3. **Chống gãy dòng bảng biểu (Table Row Integrity):** Mọi hàng bảng đều được nhúng thuộc tính OpenXML `w:cantSplit` nhằm ngăn chặn hiện tượng hàng bị cắt đôi giữa hai trang giấy. Hàng tiêu đề bảng được bổ sung `w:tblHeader` để tự động lặp lại khi bảng kéo dài qua nhiều trang.
4. **Vị trí và Phong cách Chú thích:** Chú thích bảng biểu đặt ở phía TRÊN bảng (căn trái, in nghiêng); chú thích hình ảnh và sơ đồ đặt ở phía DƯỚI hình (căn giữa, in nghiêng), có đánh số thứ tự phân cấp theo chương (Hình 2.1, Bảng 2.1...).
5. **Mục lục chấm dẫn (TOC Dot Leaders):** Mục lục được định dạng chuẩn với tiêu đề phần in đậm, các tiểu mục thụt lề 2-4 khoảng trắng, chuỗi dấu chấm dẫn cách đều và số trang khớp tại các đề mục đã kiểm tra với số trang kết xuất từ Microsoft Word.

---

## 3. THÔNG SỐ VÀ MÃ BĂM TÀI LIỆU KẾT XUẤT CUỐI CÙNG (FROZEN ARTIFACTS)

| Tên tệp tài liệu | Số trang (Word / PDF) | Kích thước (Bytes) | Mã băm SHA-256 | Trạng thái thẩm định |
| :--- | :---: | :---: | :--- | :---: |
| `BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx` | 35 trang | 1.992.544 | `249d4be26f97a810f94cbbbdb88d396326c8b92247ab23d10e3387d26708837b` | **VALIDATED (0 ERRORS)** |
| `NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx` | 11 trang | 45.654 | `d3945919aefb05b4ba6726b8bd8752a8630337092ef135f8022ea5367ea615f5` | **VALIDATED (0 ERRORS)** |
| `BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.pdf` | 35 trang | 1.386.959 | `b7e556f338f584545a1f78f3496eb60ccbece550b62fe7921756b4a5f322ea85` | QA Layout Passed |
| `NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.pdf` | 11 trang | 215.812 | `32e2be87...` | QA Layout Passed |

*Ghi chú:* Sau khi kết xuất và kiểm tra trang, hai tệp DOCX chính thức đã được **đóng băng (freeze)**, không thực hiện chỉnh sửa thêm.

---

## 4. KIỂM TOÁN CƠ SỞ DỮ LIỆU CHÍNH VÀ TẬP TIN BẰNG CHỨNG (TWO-WAY AUDIT)

### 4.1. Trạng thái cơ sở dữ liệu `cheating_system.db`
- **Kích thước tệp:** `303.104 bytes`
- **Mã băm SHA-256 trước vòng này:** `5f614f3754a96f6e55da5241e80ce4d08f6c5ee65071a50a2df16d7541780720`
- **Mã băm SHA-256 sau vòng này:** `5f614f3754a96f6e55da5241e80ce4d08f6c5ee65071a50a2df16d7541780720` (Trùng khớp tuyệt đối, chứng minh CSDL không bị thay đổi).
- **Tổng số bản ghi sự cố:** 439 bản ghi.
- **Tệp WAL/SHM:** Kích thước 0 byte.

### 4.2. Kết quả kiểm toán đối chiếu hai chiều (Two-Way Clip Matching)
Phép kiểm toán đối chiếu hai chiều giữa CSDL SQLite và thư mục `./data/evidence/` xác nhận:
- **Tổng số bản ghi sự cố trong CSDL:** **439 bản ghi**.
- **Số bản ghi có trường `video_path`:** **416 bản ghi** (23 bản ghi cờ vàng hoặc kiểm thử sớm không lưu clip).
- **Số đường dẫn tham chiếu tới clip đọc được trên đĩa:** **382 clip** (tồn tại trên đĩa, kích thước hợp lệ, đọc được qua OpenCV).
- **Số đường dẫn thiếu hoặc không đọc được:** **34 bản ghi** (thuộc các phiên kiểm thử sớm, đường dẫn được ghi vào DB nhưng tệp video tạm thời chưa được lưu bền vững hoặc đã dọn dẹp trước đó).
- **Tổng số tệp MP4 thực tế tồn tại trên đĩa trong `./data/evidence/`:** **422 tệp**.
- **Số tệp MP4 chưa ghép được với bản ghi hiện hành:** **40 tệp** (40 tệp MP4 tồn tại trên đĩa nhưng không nằm trong danh sách 416 đường dẫn của CSDL hiện hành).

---

## 5. BẰNG CHỨNG KỸ THUẬT VÀ NGUỒN GỐC CÁC SỐ LIỆU ĐO ĐẠC

### 5.1. Tuyên bố có giới hạn về chỉ số mAP@0.5
> *"Báo cáo phiên bản trước ghi nhận mAP@0.5 = 0,7858 trên tập validation nội bộ. Trong lần rà soát hồ sơ này, nhóm chưa tìm thấy log đánh giá hoặc tệp kết quả huấn luyện gốc để tái lập độc lập chỉ số; do đó số liệu được giữ dưới dạng kết quả kế thừa có dẫn nguồn, không phải kết quả được vòng kiểm toán hiện tại xác nhận lại."*

### 5.2. Phân định rõ ràng các chỉ số tốc độ và thông lượng (FPS Breakdown)
Căn cứ tệp nhật ký đo lường thô `reports/evidence/report_runtime/e2e_benchmark_result.json` (phiên đo 125,1 giây):
1. **Capture rate (Tốc độ thu nhận khung hình của camera):** $1.952\text{ khung hình} / 125,1\text{ giây} \approx 15,60\text{ khung hình/giây}$ (tốc độ tức thời trung bình đo được là 15,88 FPS).
2. **Detection results received (Số kết quả suy luận AI quan sát theo wall-clock):** Nhận được 354 kết quả suy luận trong 125,1 giây $\approx 2,83\text{ kết quả/giây}$ theo thời gian thực wall-clock.
3. **Processing-rate ratio (Tỷ lệ nghịch của độ trễ tính toán):** Độ trễ suy luận trung bình của mô hình trên CPU là $360,4\text{ ms}$, tương đương $1000\text{ ms} / 360,4\text{ ms} \approx 2,77\text{ lượt xử lý trên mỗi giây tính toán}$ (`inferences/compute-second`). Đây là chỉ số phản ánh năng lực xử lý tuần tự của mô hình trên CPU, **không được gọi là throughput quan sát theo wall-clock của toàn hệ thống**.
4. **Superseded rate (Tỷ lệ thay thế khung hình cũ):** $1.662\text{ khung hình} / 1.949\text{ khung hình nạp} = 85,3\%$ số khung hình cũ được thay thế chủ đích trong bộ đệm một phần tử (Single-Slot Buffer) để ngăn ngừa hiện tượng trễ tích lũy.

### 5.3. Các thông số kỹ thuật khác
- **Tham số ngắt chuỗi gián đoạn 0,75 giây:** `max_gap_seconds = 0.75` trong `TemporalPostureTracker` (`backend/services/temporal_tracker.py:28`). Khi chuỗi nhận diện bị mất dấu quá 0,75s, bộ đếm thời gian nghi vấn đặt lại về 0 (không sử dụng làm mịn EMA).
- **Ngưỡng kích hoạt cờ Đỏ quay đầu:** `HEAD_TURN_THRESHOLD_SECONDS = 1.25` (`backend/services/temporal_tracker.py:27`).
- **Cửa sổ Pre-roll 5 giây và Post-roll 10 giây:** `PRE_ROLL_SECONDS = 5.0`, `POST_ROLL_SECONDS = 10.0` (`backend/services/ring_buffer.py:47-48`).
- **Đồng bộ tham số Runtime không cần khởi động lại:** `save_settings` trong `backend/routers/settings.py:43-60` cập nhật trực tiếp tại runtime khi giám thị bấm Lưu trên giao diện web.
- **Phát lại clip đúng tốc độ 1.0x:** Cơ chế tái lấy mẫu lưới thời gian đều (Uniform Time-Grid Nearest-Neighbor Resampling) trong `backend/services/ring_buffer.py:464-498` chọn khung hình thực tế gần nhất với mốc thời gian danh định và xuất ở 15 FPS chuẩn qua OpenH264 DLL (không thực hiện nội suy khung hình quang học).

---

## 6. DANH SÁCH TỆP TIN TRONG GÓI BÀN GIAO (HANDOFF PACKAGE)

Gói bàn giao chính thức được nén tại tệp:  
[deliverables/ha_noi/FINAL_HA_NOI_HANDOFF.zip](file:///c:/Users/Administrator/Documents/Codespace/aiexam/deliverables/ha_noi/FINAL_HA_NOI_HANDOFF.zip)

**Danh mục tệp tin duy nhất có trong ZIP (đúng 7 thành phần theo yêu cầu):**
1. `BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx` (Báo cáo KHKT chính thức, 35 trang)
2. `NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx` (Nhật ký xây dựng sản phẩm, 11 trang)
3. `FINAL_DOCUMENT_AUDIT.md` (Báo cáo kiểm toán và nghiệm thu hồ sơ)
4. `EVIDENCE_MAP.md` (Ma trận đối chiếu bằng chứng kỹ thuật)
5. `SCREENSHOT_INDEX.md` (Danh mục phân loại hình ảnh và sơ đồ kỹ thuật)
6. `validation_report_academic.txt` (Báo cáo kiểm định cấu trúc tự động qua kỹ năng vietnamese-docs-style)
7. `screenshots/` (Thư mục chứa đúng các hình ảnh được tài liệu sử dụng, không chứa tệp dư thừa):
   - `camera_monitoring_grid.png`
   - `live_monitor_multi_cam.png`
   - `incident_matrix_panel.png`
   - `video_evidence_modal.png`
   - `ai_settings_view.png`
   - `architecture_pipeline_diagram.png`
   - `ring_buffer_time_window.png`
   - `pose_heuristic_diagram.png`

*Ghi chú bảo mật:* Tuyệt đối không đưa mã nguồn (`src/`, `backend/`), tệp mô hình (`model/`), cơ sở dữ liệu (`cheating_system.db`) hay dữ liệu định danh cá nhân vào gói ZIP bàn giao.
