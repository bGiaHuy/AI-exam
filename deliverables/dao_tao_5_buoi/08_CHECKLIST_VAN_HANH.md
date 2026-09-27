# Checklist lớp học và demo

## Người kỹ thuật chuẩn bị trước khóa

- [ ] Xác nhận commit/worktree dùng để dạy; ghi riêng các thay đổi chưa được nghiệm thu.
- [ ] Tạo bản dữ liệu đào tạo; không dùng DB vận hành để học viên bấm xác nhận/bỏ qua.
- [ ] Kiểm tra Python environment và npm dependencies đã có sẵn.
- [ ] Kiểm tra camera được hệ điều hành và trình duyệt cấp quyền.
- [ ] Chọn `SINGLE_CAMERA` cho bài đầu; chỉ mở nhiều camera sau khi đã thử thiết bị thật.
- [ ] Xác nhận `VITE_DEMO_MODE` và `DEMO_READ_ONLY`; ghi rõ buổi nào dùng dữ liệu giả lập/chỉ đọc.
- [ ] Kiểm tra cổng 8000 và 3000 chưa bị ứng dụng khác dùng.
- [ ] Chạy `start.ps1` trên máy đã chuẩn bị; kiểm tra `http://localhost:8000/api/health` và giao diện `http://localhost:3000`.
- [ ] Mở thử ít nhất hai clip dự phòng bằng chính trình duyệt/máy dùng để dạy.
- [ ] Chuẩn bị bản sao chỉ đọc của `args.yaml`, `results.csv`, `lineage_manifest.json`.
- [ ] In hoặc sao chép phiếu thực hành; tách đáp án khỏi đề kiểm tra.
- [ ] Ghi phiên bản checkpoint, threshold, camera, độ phân giải và thời điểm test.

## Học viên kiểm tra trước thực hành

- [ ] Nói được nguồn đang xem là webcam, video ghi trước hay dữ liệu giả lập.
- [ ] Hình ảnh thay đổi theo thời gian và đúng camera dự kiến.
- [ ] Backend/WebSocket không báo mất kết nối kéo dài.
- [ ] Không chỉnh model, weights, DB gốc hoặc file bằng chứng.
- [ ] Khi gán nhãn, làm trên bản sao bài tập và lưu người review.
- [ ] Khi đọc metric, ghi đúng split và version.
- [ ] Khi duyệt incident, chỉ thao tác trên dữ liệu đào tạo.

## Kết thúc buổi

- [ ] Thu đủ sản phẩm học tập; không chỉ thu bài trắc nghiệm.
- [ ] Dừng dịch vụ bằng `stop.ps1` hoặc quy trình đã thống nhất.
- [ ] Không xóa bằng chứng hay DB để “dọn máy”.
- [ ] Ghi lỗi, điều kiện và bước tái hiện; phân loại data/model/system nếu có thể.
- [ ] Sao lưu bài học viên vào thư mục khóa học, không trộn với dataset/model của project.

`start.ps1` mở backend/frontend và trình duyệt; quy trình này được suy ra từ launcher, chưa được chạy lại trong vòng soạn tài liệu. Người phụ trách phải test trên máy dự thi trước khi coi là hướng dẫn đã nghiệm thu.
