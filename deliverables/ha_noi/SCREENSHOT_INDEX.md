# DANH MỤC HÌNH ẢNH GIAO DIỆN VÀ SƠ ĐỒ KỸ THUẬT (SCREENSHOT INDEX)
### Dự án: Hệ Thống Hỗ Trợ Giám Sát Phòng Thi Bằng Thị Giác Máy Tính & Trích Xuất Video Bằng Chứng
### Hồ sơ dự thi KHKT Hà Nội — Đơn vị: Nhóm nghiên cứu

Tài liệu này kiểm toán và phân loại chi tiết toàn bộ hình ảnh và sơ đồ kỹ thuật được sử dụng trong Báo cáo Nghiên cứu KHKT và Nhật ký sản phẩm, phân định rành mạch giữa **Ảnh giao diện chạy cục bộ (Nhóm A)** và **Sơ đồ kỹ thuật minh họa (Nhóm B)**, ghi rõ thời điểm chụp, URL/màn hình, thao tác người dùng, nguồn dữ liệu, tính chất camera/video và giới hạn diễn giải khoa học.

---

## NHÓM A: ẢNH GIAO DIỆN CHẠY CỤC BỘ (LOCAL UI SCREENSHOTS)

Các ảnh trong nhóm này được chụp trực tiếp từ trình duyệt web kết nối với hệ thống đang vận hành tại máy trạm (`http://localhost:3000` kết nối Backend FastAPI `http://localhost:8000`), phản ánh giao diện và dữ liệu thực tế tại thời điểm chụp trong phiên đo kiểm ngày 25/09/2026.

| Số hình | Tên tệp ảnh | Thời điểm chụp | URL / Màn hình | Thao tác người dùng để mở màn hình | Nguồn dữ liệu đang hiển thị | Tính chất Camera / Dữ liệu | Giới hạn diễn giải khoa học |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **Hình 2.4** | `camera_monitoring_grid.png` | 25/09/2026<br>18:20:30 GMT+7 | `http://localhost:3000/`<br>(Lưới giám sát camera) | Mở trang chủ mặc định của ứng dụng trên trình duyệt web. | Khung hình thời gian thực từ webcam máy trạm và 2 luồng video kiểm thử; chỉ số HUD (FPS, Camera Status) từ WebSocket nhị phân. | Có sử dụng 01 webcam tích hợp máy trạm; 02 luồng còn lại là video kiểm thử giả lập phần mềm (Synthetic streams). Không có camera vật lý thứ hai. | Minh họa giao diện chia lưới đa luồng của giám thị; chưa phải buổi thi chính thức tại hội đồng thi. |
| **Hình 2.5** | `live_monitor_multi_cam.png` | 25/09/2026<br>18:20:45 GMT+7 | `http://localhost:3000/`<br>(Bảng điều khiển toàn màn hình) | Để nguyên giao diện trang chủ ở độ phân giải màn hình 1600x1000. | Luồng video máy trạm kết hợp ma trận danh sách sự cố đọc trực tiếp từ CSDL SQLite `cheating_system.db`. | Sử dụng webcam máy trạm và dữ liệu CSDL cục bộ (chứa 439 sự cố lịch sử và kiểm thử). | Thể hiện bố cục giao diện tổng thể của giám thị; các cảnh báo cờ đỏ trong hình sinh ra từ kịch bản kiểm thử cục bộ. |
| **Hình 2.6** | `incident_matrix_panel.png` | 25/09/2026<br>18:21:00 GMT+7 | `http://localhost:3000/`<br>(Bảng ma trận sự cố cột phải) | Quan sát khu vực danh sách sự cố bên cột phải màn hình chính. | Dữ liệu thật từ bảng `incidents` trong CSDL SQLite `cheating_system.db` gồm mã sự cố, mốc thời gian, loại vi phạm, điểm tin cậy. | Đọc từ CSDL cục bộ (chứa cả sự kiện từ webcam và kịch bản test trước đó). Không yêu cầu camera trực tiếp cho bảng này. | Minh họa các thẻ sự cố vi phạm cờ Đỏ, điểm số confidence chuẩn hóa và các nút bấm thẩm tra của giám thị. |
| **Hình 2.7** | `video_evidence_modal.png` | 25/09/2026<br>18:21:15 GMT+7 | `http://localhost:3000/`<br>(Hộp thoại bằng chứng vi phạm) | Bấm chuột vào nút "Xem Clip" trên thẻ sự cố vi phạm cờ đỏ bất kỳ trong danh sách sự cố. | Tệp video MP4 thực tế lưu tại `./data/evidence/` được phát qua thẻ HTML5 video, kèm thông tin mã sự cố và timestamp. | Video trích xuất từ cơ chế RingBuffer cục bộ ghi lại trước đó bằng OpenH264; tốc độ phát chuẩn 1.0x qua tái lấy mẫu lưới thời gian. | Minh họa chức năng phát lại video trích xuất bằng chứng cho giám thị xem lại; không phải phiên xử lý vi phạm thực tế. |
| **Hình 2.8** | `ai_settings_view.png` | 25/09/2026<br>18:37:45 GMT+7 | `http://localhost:3000/`<br>(Màn hình cấu hình độ nhạy AI) | Bấm chuột vào biểu tượng bánh răng Cài đặt trên thanh điều hướng đầu trang. | Dữ liệu cấu hình đọc trực tiếp từ tệp bền vững `./backend/data/ai_settings.json` thông qua API `GET /api/settings`. | Không sử dụng camera; hiển thị các thanh trượt tham số (Confidence, Head Turn Threshold, Pre/Post-roll). | Giao diện cấu hình runtime; việc thay đổi tham số được đồng bộ ngay lập tức vào bộ nhớ mà không cần khởi động lại dịch vụ. |

---

## NHÓM B: SƠ ĐỒ KỸ THUẬT MINH HỌA (TECHNICAL DIAGRAMS)

Các hình ảnh trong nhóm này là **sơ đồ kỹ thuật được tạo bằng mã nguồn lập trình đồ họa (Python Matplotlib, độ phân giải 300 DPI)** nhằm mục đích trực quan hóa cấu trúc kiến trúc, luồng điều phối dữ liệu và thuật toán toán học theo đúng mã nguồn dự án.

> **Cảnh báo minh bạch học thuật:**
> - Tuyệt đối không gọi Nhóm B là "ảnh chụp màn hình thực tế" hay "ảnh chụp giao diện".
> - Không gọi các luồng video kiểm thử phần mềm là camera vật lý thứ hai hay thứ ba.

| Số hình | Tên tệp ảnh | Nội dung kỹ thuật biểu diễn | Căn cứ mã nguồn thực tế | Phương thức tạo ảnh | Mục đích minh chứng |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **Hình 2.1** | `architecture_pipeline_diagram.png` | Sơ đồ kiến trúc điều phối hai luồng xử lý độc lập: Luồng 1 (Video RingBuffer 15 FPS) và Luồng 2 (Suy luận AI Single-Slot theo nhịp đệm đơn). | `backend/services/ring_buffer.py`<br>`backend/services/fair_scheduler.py` | Lập trình Python Matplotlib vector 300 DPI | Minh họa cơ chế phân tách luồng để loại bỏ hiện tượng trễ tích lũy khung hình trên máy trạm thông thường. |
| **Hình 2.2** | `ring_buffer_time_window.png` | Sơ đồ cửa sổ thời gian trích xuất bằng chứng: Pre-roll 5,0 giây trước sự kiện và Post-roll 10,0 giây sau sự kiện (*t*<sub>event</sub>). | `backend/services/ring_buffer.py`<br>(Hàm `trigger_clip_recording`) | Lập trình Python Matplotlib vector 300 DPI | Minh họa trực quan nguyên lý cắt clip dựa trên mốc thời gian UTC thực thay vì đếm số khung hình cố định. |
| **Hình 2.3** | `pose_heuristic_diagram.png` | Sơ đồ 17 điểm mốc khung xương YOLO Pose và quy tắc tính điểm nghi vấn hình học 2D kèm ngưỡng gián đoạn `max_gap_seconds = 0,75 giây`. | `backend/routers/ai_engine.py`<br>`backend/services/temporal_tracker.py` | Lập trình Python Matplotlib vector 300 DPI | Trực quan hóa công thức toán học tính điểm nghi vấn tư thế và điều kiện leo thang cờ Vàng / cờ Đỏ (*t* ≥ 1,25 giây). |

---

## NGUYÊN TẮC BẢO VỆ DỮ LIỆU VÀ ĐẠO ĐỨC KHOA HỌC

1. **Bảo vệ quyền riêng tư:** Toàn bộ ảnh giao diện không hiển thị danh tính cá nhân, họ tên, số báo danh, căn cước công dân của bất kỳ học sinh nào. Mã bám vết duy nhất là `track_id` số nguyên tự động tăng.
2. **Không làm sai lệch bản chất dữ liệu:** Không gọi dữ liệu thử nghiệm trong phòng lab là kết quả từ kỳ thi THPT Quốc gia; không gọi luồng video giả lập là camera vật lý thứ hai.
3. **Trạng thái nghiệm thu phần cứng:** Nghiệm thu đồng thời hai camera vật lý: **HARDWARE ACCEPTANCE PENDING** (ba ô hiển thị trên giao diện kiểm thử thực chất là 01 webcam vật lý kết hợp 02 luồng kiểm thử phần mềm; không suy diễn giao diện ba ô thành hệ thống ba camera vật lý).
