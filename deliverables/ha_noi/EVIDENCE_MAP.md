# MA TRẬN ĐỐI CHIẾU BẰNG CHỨNG KỸ THUẬT (EVIDENCE MAP)
### Dự án: Hệ Thống Hỗ Trợ Giám Sát Phòng Thi Bằng Thị Giác Máy Tính & Trích Xuất Video Bằng Chứng
### Hồ sơ dự thi KHKT Hà Nội — Đơn vị: Nhóm nghiên cứu

Tài liệu này đối chiếu từng chức năng cốt lõi (F-01 đến F-07), số liệu thực nghiệm, quy tắc chuẩn hóa và kiến trúc hệ thống với các bằng chứng thực tế tại mã nguồn, lịch sử Git, cơ sở dữ liệu và các tệp nhật ký kiểm thử của dự án.

---

## 1. MA TRẬN 7 CHỨC NĂNG CỐT LÕI (F-01 ĐẾN F-07)

| Mã CN | Tên chức năng thống nhất | Căn cứ mã nguồn thực tế | Bằng chứng kiểm thử / Dữ liệu | Hình ảnh minh chứng | Giới hạn khoa học & Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **F-01** | Tiếp nhận và hiển thị đa luồng camera trực tiếp | `backend/services/camera_manager.py`<br>`backend/services/camera_source.py`<br>`src/components/StreamlinedProctorDashboard.tsx` | WebSocket nhị phân truyền khung hình JPEG; HUD cập nhật tốc độ lấy mẫu camera và trạng thái | `camera_monitoring_grid.png`<br>`live_monitor_multi_cam.png`<br>(Nhóm A) | Đã kiểm thử với webcam máy trạm và 2 luồng kiểm thử synthetic. Nghiệm thu đồng thời hai camera vật lý: **HARDWARE ACCEPTANCE PENDING** (ba ô hiển thị trên giao diện kiểm thử thực chất là 01 webcam vật lý kết hợp 02 luồng kiểm thử phần mềm; không suy diễn giao diện ba ô thành hệ thống ba camera vật lý). |
| **F-02** | Phát hiện điện thoại di động trong khu vực làm bài | `backend/routers/ai_engine.py`<br>`model/weights/phone_detector_v5.pt` | Báo cáo phiên bản trước ghi nhận mAP@0.5 = 0,7858 trên tập validation nội bộ (Nguồn 1 Bảng 7); trong lần rà soát này số liệu được giữ dưới dạng kết quả kế thừa có dẫn nguồn | `live_monitor_multi_cam.png`<br>(Thẻ cảnh báo cờ đỏ PHONE) | Nhóm chưa tìm thấy log đánh giá hoặc tệp kết quả huấn luyện gốc để tái lập độc lập chỉ số; số liệu chưa được vòng kiểm toán hiện tại xác nhận lại độc lập. |
| **F-03** | Phân tích tư thế và phát hiện hành vi quay đầu nghi vấn | `backend/routers/ai_engine.py`<br>`backend/services/temporal_tracker.py`<br>`model/weights/yolo11m-pose.pt` | 17 điểm mốc COCO; ngưỡng gián đoạn `max_gap_seconds = 0.75s`; cờ Vàng khi $S \ge 0.50$; leo thang cờ Đỏ khi $t \ge 1.25$s | `pose_heuristic_diagram.png`<br>(Sơ đồ kỹ thuật Nhóm B) | Heuristic hình học 2D trên mặt phẳng ảnh, chưa đo góc quay 3D Euler; nhạy cảm với góc đặt camera từ trên cao xuống. |
| **F-04** | Bộ đệm vòng và trích xuất clip bằng chứng chuẩn tốc độ 1.0x | `backend/services/ring_buffer.py`<br>`openh264-2.5.0-win64.dll` | Hàng đợi RAM deque; Pre-roll 5.0s, Post-roll 10.0s; thuật toán Uniform Time-Grid Resampling 15 FPS; 382 clip đọc được liên kết DB | `ring_buffer_time_window.png` (Nhóm B)<br>`video_evidence_modal.png` (Nhóm A) | Tái lấy mẫu lưới thời gian đều (nearest-neighbor), không thực hiện nội suy quang học; đảm bảo phát lại đúng nhịp thời gian thực 1.0x trên trình duyệt. |
| **F-05** | Quản lý và lưu trữ sự cố an toàn bằng SQLite WAL | `backend/database.py`<br>`backend/services/db_queue.py`<br>`backend/confidence.py` | SQLite WAL (`PRAGMA journal_mode=WAL`); luồng ghi tuần tự `DBWriteQueue`; CSDL có 439 bản ghi | Lược đồ Bảng 2.2 trong báo cáo; tệp `cheating_system.db` | CSDL lưu cục bộ trên máy trạm proctor; chưa hỗ trợ đồng bộ mạng phân tán liên phòng. |
| **F-06** | Thẩm tra sự cố vi phạm và phê duyệt của giám thị | `backend/routers/incidents.py`<br>`src/components/StreamlinedProctorDashboard.tsx`<br>`src/components/VideoEvidenceModal.tsx` | API RESTful `GET /api/incidents`, `PATCH /api/incidents/{id}/confirm`; cập nhật bất biến React 19 | `incident_matrix_panel.png`<br>`video_evidence_modal.png`<br>(Nhóm A) | Giám thị thẩm tra từng sự cố trực tiếp trên giao diện máy trạm; AI chỉ giữ vai trò hỗ trợ cung cấp chứng cứ khách quan. |
| **F-07** | Cấu hình động độ nhạy AI và tham số ghi hình | `backend/routers/settings.py`<br>`src/components/AISettingsView.tsx`<br>`backend/data/ai_settings.json` | API `GET / PUT /api/settings`; lưu bền vững JSON; đồng bộ runtime không cần khởi động lại máy chủ | `ai_settings_view.png`<br>(Nhóm A) | Người vận hành cần hiểu rõ ý nghĩa tham số; đặt ngưỡng quá nhạy sẽ làm tăng số lượng cảnh báo cờ Vàng cần rà soát. |

---

## 2. MA TRẬN ĐỐI CHIẾU CÁC SỐ LIỆU ĐO ĐẠC THỰC NGHIỆM

| Số liệu thực tế | Giá trị ghi nhận | Nguồn đối chiếu kỹ thuật | Diễn giải ngữ cảnh và Bằng chứng |
| :--- | :--- | :--- | :--- |
| **Thời lượng phiên đo thông lượng** | 125,1 giây | `e2e_benchmark_result.json`, Báo cáo gốc Bảng 9 | Phiên chạy đo tải liên tục trên máy trạm cấu hình CPU. |
| **Tốc độ camera gửi (Sent)** | 1.952 khung hình (15,60 FPS) | `e2e_benchmark_result.json` | Tốc độ thu nhận hình ảnh từ camera máy trạm (Capture rate). |
| **Tốc độ máy chủ nhận (Recv)** | 1.949 khung hình (15,58 FPS) | `e2e_benchmark_result.json` | Tốc độ nạp khung hình vào hệ thống xử lý. |
| **Tốc độ thu nhận tức thời (Acq FPS)** | 15,88 FPS (Target 15 FPS) | `e2e_benchmark_result.json` | Tốc độ thu nhận tức thời trung bình của pipeline camera. |
| **Số kết quả suy luận AI nhận về** | 354 kết quả (~2,83 kết quả/giây) | `e2e_benchmark_result.json` | Số kết quả suy luận AI thực tế quan sát được theo wall-clock (354 / 125,1s). |
| **Tỷ lệ nghịch độ trễ tính toán** | 2,77 lượt xử lý/giây tính toán | `e2e_benchmark_result.json` | Tương đương $1000\text{ ms} / 360,4\text{ ms} \approx 2,77$ inference/compute-second. Không phải throughput realtime wall-clock của toàn hệ thống. |
| **Độ trễ xử lý suy luận trung bình** | 360,4 ms | `e2e_benchmark_result.json` | Thời gian xử lý trung bình của mô hình học sâu trên CPU cho một khung hình. |
| **Số khung hình thay thế chủ đích** | 1.662 khung hình (85,3%) | `e2e_benchmark_result.json` | Cơ chế Single-Slot Buffer thay thế chủ đích khung hình cũ để ngăn ngừa trễ tích lũy. |
| **Thời lượng kiểm thử đa camera** | 62,0 giây | `benchmark_640x480.log`<br>`benchmark_1920x1080.log` | Đo mức tiêu hao bộ nhớ RAM trong 2 kịch bản Scenario A và B. |
| **Bộ kiểm thử tự động Backend** | 83 bài test (83/83 PASS) | `backend_all_tests.log`, `acceptance_summary.json` | Kiểm thử RingBuffer, DBWriteQueue, CameraManager, Confidence Contract. |
| **Bộ kiểm thử toán học Evaluation** | 22 bài test (22/22 PASS) | `acceptance_summary.json` | Kiểm thử công thức ma trận nhầm lẫn và chỉ số đánh giá. |
| **Bộ kiểm thử Frontend Dual-Cam** | 15 bài test (15/15 PASS) | `acceptance_summary.json` | Kiểm thử logic điều phối hai nguồn video phía giao diện người dùng. |
| **Cửa sổ thời gian RingBuffer** | Pre-roll 5.0s, Post-roll 10.0s | `backend/services/ring_buffer.py:47-48` | Cửa sổ thời gian ghi nhận bối cảnh trước và sau sự kiện cờ Đỏ. |
| **Thời lượng clip MP4 bằng chứng** | Danh định ~15.0 giây (Tốc độ 1.0x) | Thư mục `./data/evidence/*.mp4` | Clip trích xuất qua Uniform Time-Grid Resampling và OpenH264 DLL. |
| **Tổng số bản ghi CSDL hiện tại** | 439 sự cố | `cheating_system.db` (bảng `incidents`) | Baseline 425 bản ghi + 14 bản ghi mới sinh ra từ phiên kiểm thử webcam ngày 25/09/2026. |
| **Bản ghi có `video_path`** | 416 bản ghi | Phép kiểm toán đối chiếu hai chiều | 23 bản ghi cờ vàng hoặc kiểm thử ban đầu không có clip. |
| **Số clip đọc được liên kết DB** | 382 clip | Phép kiểm toán đối chiếu hai chiều | Tệp MP4 tồn tại trên đĩa, dung lượng hợp lệ, đọc được qua OpenCV. |
| **Số clip thiếu (được DB tham chiếu)** | 34 bản ghi | Phép kiểm toán đối chiếu hai chiều | Các bản ghi thử nghiệm ban đầu, đường dẫn có trong DB nhưng tệp chưa được lưu bền vững. |
| **Tổng số tệp MP4 thực tế trên đĩa** | 422 tệp | Phép kiểm toán đối chiếu hai chiều | Toàn bộ tệp `.mp4` trong thư mục `./data/evidence/` đều hợp lệ, không có tệp nào $\le 100$ bytes. |
| **Tệp MP4 chưa ghép được với bản ghi** | 40 tệp | Phép kiểm toán đối chiếu hai chiều | 40 tệp MP4 tồn tại trên đĩa nhưng không được 416 incident hiện hành trong DB tham chiếu. |
| **Dung lượng và Hash CSDL** | 303.104 bytes<br>SHA256: `5f614f37...` | `scripts/audit_current_db.py` | Kiểm tra toàn vẹn CSDL SQLite; chế độ WAL hoạt động bình thường (WAL/SHM kích thước 0 byte). |

---

## 3. QUY TẮC CHUẨN HÓA ĐỘ TIN CẬY (CANONICAL CONFIDENCE CONTRACT)

Hợp đồng dữ liệu `backend/confidence.py` (kiểm chứng qua `backend/tests/test_confidence_contract.py`) quy định:
1. **Giá trị trong $[0.0, 1.0]$:** Giữ nguyên giá trị thực.
2. **Giá trị trong $(1.0, 100.0]$:** Chia cho 100.0 để chuyển đổi về đoạn $[0.0, 1.0]$.
3. **Giá trị âm ($< 0.0$):** **TỪ CHỐI** bằng ngoại lệ `InvalidConfidenceError`. Hệ thống **KHÔNG ÉP KIỂU (KHÔNG CLAMP)** về 0.
4. **Giá trị sai quy chuẩn:** Giá trị $> 100.0$, `NaN`, `Inf`, `bool`, `None` hoặc chuỗi ký tự phi số đều bị **TỪ CHỐI** bằng `InvalidConfidenceError`.

---

## 4. TÌNH TRẠNG NGHIỆM THU PHẦN CỨNG CAMERA (HARDWARE MATRIX)

| Cấp độ kiểm thử | Đối tượng kiểm thử | Kết quả thực tế | Trạng thái nghiệm thu |
| :--- | :--- | :--- | :---: |
| **Khả năng cấu hình kiến trúc** | Hỗ trợ hệ thống hai camera đồng thời | Đã lập trình trong `CameraManager` và `FairInferenceScheduler` | **ĐÃ XÁC MINH (Code)** |
| **Kiểm thử phần mềm giả lập (Synthetic)** | 2 luồng video kiểm thử đồng thời | Đạt yêu cầu trong Sprint 3.2B-R2 (15 tests frontend pass) | **ĐÃ XÁC MINH (Software)** |
| **Kiểm thử webcam vật lý đơn** | Webcam tích hợp máy trạm | Đạt yêu cầu nhận diện và hiển thị thời gian thực | **ĐÃ XÁC MINH (Workstation)** |
| **Kiểm thử đồng thời hai camera vật lý** | 2 webcam ngoài EYD PC02 | Đã đặt mua 2 webcam ngoài; đang chờ bàn giao thiết bị | **HARDWARE ACCEPTANCE PENDING** |
| **Kiểm thử tại phòng thi / hội trường** | Bố trí thực địa phòng thi | Chưa triển khai trên quy mô phòng thi thật | **CHƯA TRIỂN KHAI (Hướng phát triển)** |
