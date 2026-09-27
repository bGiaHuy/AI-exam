# Kịch bản dự phòng khi dạy và demo

Nguyên tắc: giữ đúng loại bằng chứng. Một screenshot minh họa giao diện không chứng minh inference; một clip ghi trước không chứng minh webcam đang hoạt động; dữ liệu giả lập không chứng minh model phát hiện.

| Sự cố | Kiểm tra nhanh | Phương án tiếp tục | Câu nói trung thực |
|---|---|---|---|
| Camera không có hình | Quyền camera, thiết bị khác đang chiếm, đúng device | Dùng video đầu vào đã chuẩn bị | “Camera đang lỗi, em chuyển video ghi trước làm đầu vào cho AI.” |
| Backend không chạy | Cổng 8000, terminal/log, health endpoint | Dạy bằng artifact và screenshot; không diễn inference | “Phần backend chưa hoạt động, ảnh sau đây chỉ giúp giải thích kiến trúc.” |
| WebSocket mất kết nối | Banner lỗi, URL/cổng, backend | Khởi động lại đúng quy trình nếu còn thời gian; nếu không dùng video bằng chứng độc lập | “Luồng trực tiếp chưa kết nối; em không coi phần này là demo AI thành công.” |
| Không phát hiện điện thoại | Vùng nhìn, ánh sáng, monitoring, nguồn, threshold đã ghi | Ghi nhận ca bỏ sót; chuyển clip dự phòng | “Lượt này chưa tạo detection. Đây là một quan sát cần đưa vào đánh giá.” |
| Không leo thang quay đầu | Chuỗi bị gap, track đổi, thời lượng, tốc độ inference | Dùng timeline để giải thích temporal rule | “Chuỗi quan sát có thể chưa đủ điều kiện liên tục; em cần log để xác định.” |
| Incident có nhưng clip chưa hiện | Chờ post-roll/ghi file, đường dẫn, log | Mở clip đã kiểm tra hoặc mô tả RingBuffer bằng sơ đồ | “File mới chưa hoàn tất; em chuyển clip đã ghi trước và nói rõ nguồn.” |
| Clip không phát | File tồn tại, kích thước, codec/trình duyệt | Dùng trình phát đã thử hoặc clip dự phòng khác | “Lỗi đang ở bước phát file, chưa đủ căn cứ quy cho model.” |
| DB/update trạng thái lỗi | Backend, quyền demo read-only, phản hồi API | Không bấm lặp; giữ trạng thái cũ và giải thích | “Thao tác duyệt chưa lưu thành công.” |
| Mất Internet | Phân biệt Internet với LAN camera RTSP | Dùng webcam/file local; tài liệu offline | “Luồng cốt lõi đang chạy cục bộ; RTSP vẫn cần mạng tới camera.” |
| Máy quá chậm | FPS inference, backlog/superseded, nhiệt độ | Chuyển video/clip; giảm phạm vi demo đã test | “Máy hiện không đáp ứng tốc độ dự kiến; em không suy ra chất lượng model từ lượt này.” |

Sau sự cố, ghi: thời gian; version; input; cấu hình; triệu chứng; log liên quan; bước tái hiện; lớp nghi ngờ; điều chưa biết. Không sửa threshold tùy ý trong lúc demo rồi gọi đó là “model đã tốt hơn”.
