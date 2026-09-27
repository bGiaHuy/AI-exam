# QUY TRÌNH NGHIỆM THU PHẦN CỨNG: CHẾ ĐỘ GIÁM SÁT 2 CAMERA (DUAL-CAMERA MODE)
## SPRINT 3.2 — HARDWARE ACCEPTANCE RUNBOOK & DEPLOYMENT GUIDE

---

> **TRẠNG THÁI NGHIỆM THU HIỆN TẠI (ACCEPTANCE STATUS):**  
> `HARDWARE_ACCEPTANCE: BLOCKED — chưa có hai camera RTSP thực tế trong môi trường kiểm thử`  
> *(Toàn bộ pipeline phần mềm, fair round-robin scheduler, RingBuffer đa camera, SQLite schema migration và frontend UI đã được kiểm thử tự động bằng synthetic camera stream và test suite 26/26 backend, 12/12 frontend. Bước nghiệm thu vật lý trên luồng RTSP camera thực tế tạm thời bị chặn do chưa có hai camera RTSP vật lý trong môi trường kiểm thử).*

---

## 1. MỤC TIÊU VÀ PHẠM VI HỆ THỐNG

Tài liệu này hướng dẫn kỹ thuật viên hiện trường và giám thị triển khai, cấu hình và nghiệm thu chế độ giám sát 2 camera đồng thời (**Dual-Camera Monitoring Mode**) phục vụ phòng thi trên giấy:

- **Camera 1 (Góc trước - Front View):** Đặt ngang tầm mắt hoặc phía trước phòng thi, bao quát trực diện tư thế ngồi làm bài, hỗ trợ ghi nhận hành vi cúi gằm/quay đầu trao đổi bài (`HEAD_TURNING`) và sử dụng điện thoại trước ngực (`PHONE`).
- **Camera 2 (Góc bên / Mặt bàn - Side / Desk View):** Đặt chếch góc 45° bên hông hoặc góc cao chiếu xiên xuống bàn thi, bao quát khu vực mặt bàn và thao tác tay, hỗ trợ ghi nhận hành vi sử dụng thiết bị di động (`PHONE`).

---

## 2. THIẾT BỊ PHẦN CỨNG TIÊU CHUẨN ĐƯỢC HỖ TRỢ

Hệ thống được thiết kế theo giao thức tiêu chuẩn mở (RTSP / ONVIF Profile S), khuyến nghị các dòng camera giám sát thương mại phổ biến:

| Thiết bị | Nhà sản xuất | Giao thức | Độ phân giải khuyến nghị | Tốc độ khung hình (FPS) | Mã hóa luồng |
|---|---|---|---|---|---|
| **Tapo TC70 / C200** | TP-Link | RTSP / TCP | 1080p (1920x1080) hoặc 720p | 15 FPS | H.264 |
| **Tapo TC71 / C210** | TP-Link | RTSP / TCP | 2K / 1080p | 15 FPS | H.264 |
| **USB Webcam tiêu chuẩn** | Mọi hãng (UVC) | USB DirectShow / V4L2 | 720p (1280x720) | 15 - 30 FPS | RAW / MJPEG |
| **Browser WebRTC/WS** | Workstation Client | WebSocket Binary (JPEG) | 640x360 / 720p | 15 FPS | JPEG Buffer |

---

## 3. CHÍNH SÁCH AN TOÀN MẠNG VÀ CÔ LẬP CAMERA (NETWORK ISOLATION)

Theo nguyên tắc **Offline-First & Zero-Cloud Mandate (Rule 6)**:

1. **Cô lập mạng cục bộ (Isolated VLAN / Subnet):**
   - Camera IP và máy trạm giám sát của giám thị (Proctor Workstation) phải được đặt trong cùng một dải mạng LAN nội bộ không có cổng ra Internet (VD: `192.168.100.0/24`).
   - Khóa cổng WAN trên switch/router phòng thi để ngăn camera gửi telemetry lên cloud của nhà sản xuất (TP-Link Cloud, Tuya Cloud, AWS).
2. **Bảo vệ chứng thực RTSP (Credential Safety):**
   - Đặt tài khoản camera nội bộ riêng biệt (Local Camera Account), không dùng chung mật khẩu quản trị mạng.
   - Định dạng URI RTSP chuẩn:
     ```text
     rtsp://<camera_user>:<camera_password>@192.168.100.51:554/stream1
     rtsp://<camera_user>:<camera_password>@192.168.100.52:554/stream1
     ```
   - **Tuyệt đối không lưu mật khẩu rõ ràng trong log hoặc báo cáo.** Hệ thống tự động làm mờ chứng chỉ bằng hàm `redact_url()`:
     ```text
     rtsp://***:***@192.168.100.51:554/stream1
     ```

---

## 4. HƯỚNG DẪN CẤU HÌNH CAMERA TAPO TC70 / TC71 TỪNG BƯỚC

### Bước 4.1: Bật tài khoản camera cục bộ (Local Camera Account)
1. Mở ứng dụng TP-Link Tapo trên điện thoại (chỉ cần trong lúc cài đặt ban đầu).
2. Chọn Camera -> Cài đặt thiết bị (Device Settings / biểu tượng bánh răng) -> **Cài đặt nâng cao (Advanced Settings)** -> **Tài khoản camera (Camera Account)**.
3. Tạo tài khoản cục bộ:
   - Tên người dùng: `proctor_cam1` (hoặc `proctor_cam2`)
   - Mật khẩu: `SecurePass@2026` (ví dụ)
4. Ghi lại IP tĩnh của camera do DHCP Router cấp (khuyến nghị gắn IP tĩnh theo địa chỉ MAC trên router phòng thi).

### Bước 4.2: Cấu hình biến môi trường trên Proctor Workstation
Tạo hoặc cập nhật file `.env` trên máy trạm giám sát (dựa trên mẫu `.env.example`):

```bash
# Chế độ kích hoạt 2 camera
CAMERA_MODE="DUAL_CAMERA"

# Cấu hình Camera 1 (Góc trước)
CAMERA_1_TYPE="rtsp"
CAMERA_1_LABEL="Camera 1 (Góc trước)"
CAMERA_1_RTSP_URL="rtsp://proctor_cam1:<password>@192.168.100.51:554/stream1"
CAMERA_1_FPS="15.0"

# Cấu hình Camera 2 (Góc bên / Mặt bàn)
CAMERA_2_TYPE="rtsp"
CAMERA_2_LABEL="Camera 2 (Góc bên)"
CAMERA_2_RTSP_URL="rtsp://proctor_cam2:<password>@192.168.100.52:554/stream1"
CAMERA_2_FPS="15.0"
```

---

## 5. QUY TRÌNH NGHIỆM THU VẬT LÝ 10 BƯỚC (PHYSICAL ACCEPTANCE CHECKLIST)

Khi thiết bị thực tế có mặt tại phòng thi, kỹ thuật viên thực hiện tuần tự 10 bước kiểm tra:

### Bước 1: Ping và kiểm tra kết nối mạng
```powershell
Test-NetConnection -ComputerName 192.168.100.51 -Port 554
Test-NetConnection -ComputerName 192.168.100.52 -Port 554
```
*Tiêu chí đạt:* `TcpTestSucceeded : True` cho cả hai camera.

### Bước 2: Kiểm tra bắt luồng RTSP bằng ffplay / OpenCV
```powershell
ffplay -rtsp_transport tcp "rtsp://proctor_cam1:<password>@192.168.100.51:554/stream1"
```
*Tiêu chí đạt:* Cửa sổ video hiện rõ hình ảnh góc trước, độ trễ < 500ms, không rách hình.

### Bước 3: Khởi động Backend AI Exam Server
```powershell
& ".\.venv\Scripts\python.exe" backend/main.py
```
*Tiêu chí đạt:* Server lắng nghe tại `http://localhost:8000`, terminal xuất log:
```text
[CAMERA_MANAGER] Initializing in DUAL_CAMERA mode.
[CAMERA_SOURCE:cam1] RTSP Camera Source ready: rtsp://***:***@192.168.100.51:554/stream1
[CAMERA_SOURCE:cam2] RTSP Camera Source ready: rtsp://***:***@192.168.100.52:554/stream1
[FAIR_SCHEDULER] Configured 2 sources: ['cam1', 'cam2']
```

### Bước 4: Kiểm tra API trạng thái nguồn camera
Truy vấn HTTP GET: `http://localhost:8000/api/camera/sources`  
*Tiêu chí đạt:* Trả về JSON HTTP 200:
- `mode`: `"DUAL_CAMERA"`
- `cameras`: gồm 2 object `cam1` và `cam2`, cả hai có `status: "ONLINE"`
- `total_online`: `2`
- Không có bất kỳ mật khẩu nào bị lộ trong response.

### Bước 5: Kiểm tra giao diện Proctor Dashboard (React 19)
1. Mở trình duyệt tại `http://localhost:5173`.
2. Quan sát khung camera trên Dashboard:
   - Header hiển thị toggle `1 CAMERA` | `2 CAMERA` (chế độ `2 CAMERA` được chọn).
   - Viewport hiển thị lưới 2 màn hình song song (`cam1` Góc trước, `cam2` Góc bên).
   - Đèn trạng thái hiển thị màu xanh lục `ONLINE` kèm badge tốc độ FPS thực tế (~15 FPS).

### Bước 6: Kiểm tra tính công bằng của bộ điều phối (Fair Scheduler Alternation)
1. Theo dõi log backend trong 30 giây.
2. *Tiêu chí đạt:* Số lượng frame được nạp vào AI detector luân phiên đồng đều giữa `cam1` và `cam2` (tỷ lệ phân bổ nằm trong khoảng 45% - 55%, không camera nào bị bỏ đói).

### Bước 7: Thử nghiệm tạo vi phạm trên Camera 1 (Góc trước)
1. Người thử nghiệm ngồi trước Camera 1 giơ điện thoại di động lên ngang tầm mắt hoặc quay đầu liên tục > 1.5 giây.
2. *Tiêu chí đạt:*
   - Cảnh báo cờ ĐỎ xuất hiện trên thẻ `cam1`.
   - Danh sách vi phạm (Incident List) xuất hiện thẻ vi phạm với nhãn `[Cam 1: Camera 1 (Góc trước)]`.
   - Camera 2 vẫn giữ nguyên trạng thái giám sát bình thường, không bị cảnh báo giả.

### Bước 8: Thử nghiệm tạo vi phạm trên Camera 2 (Góc bên)
1. Người thử nghiệm giơ điện thoại dưới mặt bàn trong góc quan sát của Camera 2.
2. *Tiêu chí đạt:*
   - Cảnh báo cờ ĐỎ xuất hiện trên thẻ `cam2`.
   - Thẻ vi phạm mới được ghi nhận với nhãn `[Cam 2: Camera 2 (Góc bên)]`.
   - ID vi phạm có tiền tố rõ ràng `inc_cam2_*`.

### Bước 9: Kiểm tra xuất clip bằng chứng độc lập (RingBuffer Isolation)
1. Bấm vào nút "Xem bằng chứng" (View Clip) trên thẻ vi phạm của cả 2 sự cố vừa tạo.
2. *Tiêu chí đạt:*
   - Modal hiển thị đúng video tương ứng với camera phát hiện (clip của Cam 1 chỉ chứa hình ảnh Cam 1; clip của Cam 2 chỉ chứa hình ảnh Cam 2).
   - Không bị lẫn lộn (cross-contamination) giữa hai luồng video.
   - Thời lượng video khoảng 15 giây (5s trước vi phạm + 10s sau vi phạm).

### Bước 10: Kiểm tra tính năng tự phục hồi khi mất kết nối (Reconnection Resiliency)
1. Rút dây mạng hoặc ngắt nguồn của Camera 2 trong 10 giây rồi cắm lại.
2. *Tiêu chí đạt:*
   - Backend phát hiện ngắt kết nối, chuyển trạng thái `cam2` thành `RECONNECTING`.
   - Giao diện hiển thị cảnh báo `Mất tín hiệu camera 2` với cơ chế backoff an toàn (1s, 2s, 4s... max 30s), không gây sập ứng dụng.
   - Camera 1 vẫn tiếp tục xử lý AI ở tốc độ 100% tài nguyên (Single Camera Fallback).
   - Khi cắm lại nguồn, `cam2` tự động tái kết nối thành công và chuyển về `ONLINE`.

---

## 6. DANH SÁCH BẰNG CHỨNG KIỂM THỬ PHẦN MỀM HIỆN CÓ

Trong khi chờ đợi thiết bị phần cứng thực tế, các hành vi logic của hệ thống được xác thực qua bộ kiểm thử tự động:

1. **`backend/tests/test_dual_camera_pipeline.py` (26/26 PASSED):**
   - Các trường hợp tương thích ngược chế độ `SINGLE_CAMERA` đã pass.
   - Cơ chế ngắt phiên và chuyển đổi chế độ an toàn giữa `SINGLE_CAMERA` và `DUAL_CAMERA`.
   - Làm mờ thông tin xác thực RTSP (`redact_url()`) theo RFC 3986 và kiểm tra không rò rỉ credential/marker.
   - Thuật toán vòng tròn công bằng (Round-Robin) và cơ chế zero-backlog buffer (superseded).
   - Đảm bảo tính độc lập của RingBuffer, không phát hiện rò rỉ frame giữa hai camera trong test suite.
   - Không phát hiện trùng lặp khóa chính sự cố (`inc_cam1_*` vs `inc_cam2_*`).
   - Lưu trữ đầy đủ metadata nguồn (`source_label`, `source_type`, `session_id`) vào SQLite.
   - Cách ly chuỗi trạng thái theo dõi tư thế (`temporal_posture_tracker`).
   - Khóa độc quyền WebSocket ingest `/api/ws/ingest` theo từng `source_id`.
   - Bảo vệ endpoint quản trị (`POST /api/camera/mode`, `POST /api/session/reset`) chỉ cho phép loopback cục bộ (127.0.0.1 / ::1).
2. **`backend/tests/test_refactored_system.py` (31/31 PASSED):**
   - Toàn bộ 31 unit test kiến trúc nền tảng đạt kết quả pass.
3. **`src/services/__tests__/test_frontend_dual_camera.ts` (12/12 PASSED):**
   - 12 kiểm thử frontend contract cho dual-camera, toggle mode, RingBuffer độc lập và backward compatibility đều pass.
4. **`scripts/evaluation/tests/test_evaluation_harness.py` (22/22 PASSED):**
   - Toàn bộ 22 kiểm thử harness đánh giá đạt kết quả pass.
5. **`scripts/benchmark/benchmark_dual_camera.py` (PASSED - >= 60 giây):**
   - Tỷ lệ phân bổ xử lý luân phiên xấp xỉ ~50% / 50%.
   - Invariant toán học: `submitted == processed + superseded + pending` được nghiệm chứng đầy đủ với `superseded > 0`.

---
*Biên soạn: Senior Full-stack / Computer Vision Engineer*  
*Dự án: AI-Powered Automated Proctoring System*
